# =============================== #
# == Last Update : 2026.04.11. == #
# =============================== #

import discord
from discord.ext import commands
import asyncio
import random
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from dotenv import load_dotenv
load_dotenv()

# ============================= 로그 기록 ================================= #
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(message)s')

file_handler = TimedRotatingFileHandler(
    filename='logs/reaction.log', 
    when='midnight', 
    interval=1, 
    backupCount=30,
    encoding='utf-8'
)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# ========================================================================== #


# === 환경 변수 ===
TOKEN = os.getenv('DISCORD_TOKEN')

# === 허용된 채널 ID ===
ALLOWED_CHANNELS = [
    996126079024635965, # 토모서버/내전하실분
    1298193801411821610,# 발로란트투게더/내전공지
    1298196123210612766,# 발로란트투게더/봇챗
    1475113199534735393 # 개인채널/봇테스트
]

# ========= 맵 리스트 =========
allmaps = ["스플릿", "바인드", "헤이븐", "어센트", "아이스박스", "브리즈", "프랙처", "펄", "로터스", "선셋", "어비스", "코로드"] 
maps = ["바인드", "브리즈", "스플릿", "펄", "헤이븐", "프랙처", "로터스"]

map_images = {
     "스플릿" : "스플릿.png",
     "바인드" : "바인드.png",
     "헤이븐" : "헤이븐.png",
     "어센트" : "어센트.png",
     "아이스박스" : "아이스박스.png",
     "브리즈" : "브리즈.png",
     "프랙처" : "프랙처.png",
     "펄" : "펄.png",
     "로터스" : "로터스.png",
     "선셋" : "선셋.png",
     "어비스" : "어비스.png",
     "코로드" : "코로드.png"
}

# ===== 내전 관리 클래스 =====
class InternalGame:
    def __init__(self):
        self.participants = []
        self.waiting_list = []
        self.game_date = None
        self.game_time = None

    def add_participant(self, user_id):
        if user_id not in self.participants and user_id not in self.waiting_list:
            (self.participants if len(self.participants) < 10 else self.waiting_list).append(user_id)

    def remove_participant(self, user_id):
        if user_id in self.participants:
            self.participants.remove(user_id)
            if self.waiting_list:
                self.participants.append(self.waiting_list.pop(0))
        elif user_id in self.waiting_list:
            self.waiting_list.remove(user_id)

    def set_datetime(self, date, time):
        self.game_date = date
        self.game_time = time

# ===== 봇 정의 =====
class GameBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.game = InternalGame()
        self.internal_game_message = None

    async def create_game_embed(self):
        embed = discord.Embed(title='내전 참가자 목록', color=0xff4444)
        datetime_text = f'{self.game.game_date or "미정"} {self.game.game_time or ""}'
        embed.add_field(name='일시', value=datetime_text, inline=False)
        
        p_text = '\n'.join(f'{i}. <@{p}>' for i, p in enumerate(self.game.participants, 1)) or '참가자가 없습니다.'
        embed.add_field(name='참가자 명단', value=p_text, inline=False)
        
        if self.game.waiting_list:
            w_text = '\n'.join(f'{i}. <@{p}>' for i, p in enumerate(self.game.waiting_list, 1))
            embed.add_field(name='대기자 명단', value=w_text, inline=False)
        return embed

bot = GameBot()

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# ========== 명령어 ==========
@bot.command(name='명령어')
async def help_command(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass

    embed = discord.Embed(
        title='🤖 봇 명령어 도움말',
        description='사용 가능한 명령어 목록입니다.',
        color=0x00b0f4
    )
    embed.add_field(
        name='📋 기본 명령어',
        value=(
            '`!명령어` 명령어 표시\n'
            '`!내전 [날짜] [시간]` 내전 시작\n'
            '`!삭제번호 [번호]` 참가자/대기자 삭제\n'
            '`!내전초기화` 참가자/대기자 전부 삭제\n'
            '`!순서바꾸기 [번호1] [번호2]` 참가자/대기자의 순서바꾸기\n'
            '`!내전준비` 참여자 준비 안내\n'
            '`!내전마무리` 내전 종료 안내\n'
            '`!맵` 랜덤 맵 추첨\n'
            '※ 내전은 이모지 반응으로 참가/취소'
        ), inline=False)
    embed.add_field(
        name='⚙️ 관리자 전용 명령어',
        value='`!종료` 봇 종료', inline=False
    )
    embed.add_field(
        name='⚠️ 주의사항',
        value='모든 명령어는 지정된 채널에서만 동작.', inline=False
    )
    await ctx.send(embed=embed, ephemeral=True)


# ===== 내전 시작 =====
@bot.command(name='내전')
async def start_internal_game(ctx, date=None, time=None):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass
    if not date or not time:
        await ctx.send('날짜와 시간을 입력해주세요.\n사용법: !내전 2026-01-01 20:00', delete_after=5)
        return
    bot.game.set_datetime(date, time)
    role = discord.utils.get(ctx.guild.roles, name='member')
    if not role:
        await ctx.send('member 역할을 찾을 수 없습니다.')
        return
    announcement = (
        f'{role.mention}\n'
        '```md\n'
        '📢 발로란트 내전 참가 안내\n\n'
        '내전에 참여하고 싶은 분들은 아래 **참여 이모티콘**을 눌러주세요! 😊\n\n'
        '📋 **참여 전 규칙 확인**\n'
        '1. ⁠📋│규칙 에서 **내전 규칙**을 확인하고 숙지해 주세요.\n'
        '2. ⁠📌│역할지급 에서 **티어 선택**을 완료해 주세요. *티어 선택이 되지 않을 경우 참여가 제한될 수 있습니다.*\n'
        '3. 닉네임을 닉네임 규정에 맞게 변경해주세요. *출생년도(두자리)/티어/닉네임 * \n'
        '4. 내전 참여후 취소는 내전시작 한시간 전까지 가능합니다. *불이행시 다음 내전 참여에 제한될 수 있습니다.*\n\n'
        '⚔️ **중요 사항**\n'
        '1. 참여 이모지를 누른 후 닉네임 변경은 금지됩니다.\n'
        '2. 참여자는 선착순으로 10명까지만 가능합니다.\n'
        '3. 11번째 이후 신청자는 *대기 인원*으로 등록됩니다.\n\n'
        '* 내전 알림을 원하는 멤버분들은 **📌│역할지급** 채널에 있는 내전 진행 알림 이모지를 눌러주세요!\n'
        '* 멋진 플레이 기대하겠습니다! 🎮🔥```'
    )
    await ctx.send(announcement)
    embed = await bot.create_game_embed()
    game_message = await ctx.send(embed=embed)
    bot.internal_game_message = game_message
    await game_message.add_reaction('<:1296488960255852667:1310611177092415559>')
    
# ===== 내전 참가자/대기자 삭제 =====
@bot.command(name='삭제번호')
@commands.check(is_admin)
async def remove_participant_by_number(ctx, number: int):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass
    if not bot.internal_game_message:
        await ctx.send("내전 안내 메시지를 찾을 수 없습니다.", delete_after=3)
        return
    total_p, total_w = len(bot.game.participants), len(bot.game.waiting_list)
    total = total_p + total_w
    if number < 1 or number > total:
        await ctx.send(f"잘못된 번호입니다. (1 ~ {total})", delete_after=3)
        return
    if number <= total_p:
        removed_id = bot.game.participants[number - 1]
        bot.game.remove_participant(removed_id)
    else:
        removed_id = bot.game.waiting_list[number - total_p - 1]
        bot.game.waiting_list.remove(removed_id)
        
    updated_embed = await bot.create_game_embed()
    await bot.internal_game_message.edit(embed=updated_embed)
    await ctx.send(f"<@{removed_id}> 님이 참가자/대기자 목록에서 삭제되었습니다.", delete_after=3)

@remove_participant_by_number.error
async def remove_participant_error(ctx, error):
    try: await ctx.message.delete()
    except: pass
    if isinstance(error, commands.CheckFailure):
        await ctx.send("이 명령어는 관리자만 사용할 수 있습니다.", delete_after=3)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("올바른 숫자를 입력해주세요. 사용법: !내전삭제 [번호]", delete_after=3)

# ===== 내전 초기화 (관리자) =====
@bot.command(name='내전초기화')
async def reset_internal_game(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try:
        await ctx.message.delete()
    except:
        pass
    
    bot.game.participants.clear()
    bot.game.waiting_list.clear()
    
    if bot.internal_game_message:
        try:
            await bot.internal_game_message.clear_reactions()
            await bot.internal_game_message.add_reaction('<:1296488960255852667:1310611177092415559>')
        except:
            pass
        try:
            await bot.internal_game_message.edit(embed=await bot.create_game_embed())
        except:
            pass
    await ctx.send('내전 참가자/대기자 목록을 초기화했습니다.', delete_after=3)

# ===== 참가자/대기자 순서 변경 =====
@bot.command(name='순서바꾸기')
@commands.check(is_admin)
async def swap_participants(ctx, num1: int, num2: int):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass

    if not bot.internal_game_message:
        await ctx.send("내전 안내 메시지를 찾을 수 없습니다.", delete_after=3)
        return

    all_players = bot.game.participants + bot.game.waiting_list
    total = len(all_players)

    if num1 < 1 or num1 > total or num2 < 1 or num2 > total:
        await ctx.send(f"잘못된 번호입니다. (1 ~ {total} 사이의 숫자를 입력해주세요)", delete_after=3)
        return

    if num1 == num2:
        await ctx.send("서로 다른 두 번호를 입력해주세요.", delete_after=3)
        return

    idx1, idx2 = num1 - 1, num2 - 1
    all_players[idx1], all_players[idx2] = all_players[idx2], all_players[idx1]

    bot.game.participants = all_players[:10]
    bot.game.waiting_list = all_players[10:]

    updated_embed = await bot.create_game_embed()
    await bot.internal_game_message.edit(embed=updated_embed)

    logger.info(f"[순서변경] 관리자가 {num1}번과 {num2}번 참가자의 순서를 변경했습니다.")
    await ctx.send(f"{num1}번과 {num2}번 참가자의 순서가 성공적으로 변경되었습니다.", delete_after=3)


@swap_participants.error
async def swap_participants_error(ctx, error):
    try: await ctx.message.delete()
    except: pass
    if isinstance(error, commands.CheckFailure):
        await ctx.send("이 명령어는 관리자만 사용할 수 있습니다.", delete_after=3)
    elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
        await ctx.send("올바른 형식을 입력해주세요. 사용법: !순서바꾸기 [번호1] [번호2]", delete_after=3)


# ===== 랜덤 맵 =====
@bot.command(name='맵')
async def random_map(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try:
        await ctx.message.delete()
    except:
        pass

    selected_map = random.choice(maps)
    selected_image = map_images.get(selected_map)

    embed = discord.Embed(
        title="🎲 랜덤 맵 추첨 결과 🎮",
        description=f"이번 게임의 맵은 **{selected_map}** 입니다! 🗺",
        color=0x1abc9c
    )

    if selected_image:
        file = discord.File(f"./images/{selected_image}", filename="map.png")
        embed.set_image(url="attachment://map.png")
    else:
        file = None

    embed.set_footer(text="발로란트 맵 로테이션 변경사항에 따라 랜덤하게 선택됩니다.")

    if file:
        await ctx.send(file=file, embed=embed)
    else:
        await ctx.send(embed=embed)
        
# ===== 내전 준비 =====
@bot.command(name='내전준비')
async def ready_internal_game(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass

    if not bot.game.participants:
        await ctx.send('현재 참가자가 없습니다.', delete_after=3)
        return

    mentions = [f"<@{user_id}>" for user_id in bot.game.participants]

    await ctx.send('금일 대진표입니다.\n7시 55분까지 마이크 키고 로비로 모여주세요!!\n\n' + ' '.join(mentions))

        
# ===== 내전 종료 안내 =====
@bot.command(name='내전마무리')
async def end_internal_game(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass
    role = discord.utils.get(ctx.guild.roles, name='member')
    if not role:
        await ctx.send('member 역할을 찾을 수 없습니다.', ephemeral=True)
        return
    announcement = (
        f'{role.mention}\n'
        '```**🎮 발로란트 내전 종료 안내 🔥**\n'
        '모두 고생 많으셨습니다! 😊\n\n'
        '이번 내전은 비정기적으로 진행되는 이벤트였으며, **다음 내전 일정**은 추후 공지를 통해 안내드릴 예정입니다.\n'
        '내전 진행 요일은 매번 다를 수 있으니, 참여를 희망하시는 분들은 꼭 **다음 공지**를 확인해주시길 바랍니다.\n\n'
        '함께해주셔서 감사드리며, 멋진 플레이를 보여주신 모든 분들께 다시 한번 감사의 말씀을 드립니다.\n'
        '그럼 다음 내전에서 더 멋진 모습으로 뵙겠습니다! 🎉\n\n'
        '💡 **문의 사항이 있으시면 ⁠📩│문의하기 채널을 통해 편하게 말씀해주세요!**```'
    )
    await ctx.send(announcement)

# ===== 봇 종료 (관리자) =====
@bot.command(name='종료')
@commands.check(is_admin)
async def shutdown(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    try: await ctx.message.delete()
    except: pass
    confirm_embed = discord.Embed(
        title='봇 종료 확인',
        description='정말로 봇을 종료하시겠습니까?\n계속하려면 ✅ 를 눌러주세요.\n취소하려면 ❌ 를 눌러주세요.',
        color=0xff0000
    )
    confirm_msg = await ctx.send(embed=confirm_embed, ephemeral=True)
    await confirm_msg.add_reaction('✅')
    await confirm_msg.add_reaction('❌')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        if str(reaction.emoji) == '✅':
            await ctx.send(embed=discord.Embed(title='봇 종료', description='봇을 종료합니다...', color=0xff0000), ephemeral=True)
            await bot.close()
        else:
            await ctx.send('봇 종료가 취소되었습니다.', ephemeral=True)
    except asyncio.TimeoutError:
        await ctx.send('시간이 초과되어 봇 종료가 취소되었습니다.', ephemeral=True)

@shutdown.error
async def shutdown_error(ctx, error):
    try: await ctx.message.delete()
    except: pass
    if isinstance(error, commands.CheckFailure):
        await ctx.send(embed=discord.Embed(title='권한 오류', description='이 명령어는 관리자만 사용.', color=0xff0000), ephemeral=True)

# ===== 이모지 리액션 처리 =====
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot: return
    message = reaction.message
    if not message.embeds: return
    title = message.embeds[0].title
    if title and '내전 참가자 목록' in title:
        bot.game.add_participant(user.id)
        logger.info(f"[참가] {user.display_name}({user.id}) 님이 내전 참가 이모지를 눌렀습니다.")
        await message.edit(embed=await bot.create_game_embed())

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot: return
    message = reaction.message
    if not message.embeds: return
    title = message.embeds[0].title
    if title and '내전 참가자 목록' in title:
        bot.game.remove_participant(user.id)
        logger.info(f"[취소] {user.display_name}({user.id}) 님이 내전 참가 이모지를 해제했습니다.")
        await message.edit(embed=await bot.create_game_embed())

# ===== 메시지 커맨드 처리 =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id in ALLOWED_CHANNELS:
        await bot.process_commands(message)

# ===== 봇 실행 =====
if __name__ == "__main__":
    bot.run(TOKEN)
