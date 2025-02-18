import discord
from discord.ext import commands, tasks
import sqlite3
import datetime

# Set up bot with command prefix
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# Database Connection
conn = sqlite3.connect('pet_data.db')
cursor = conn.cursor()

# Food Options
food_options = {
	"protein_fruit_smoothie": 500,
	"burger": 1000,
	"cake_and_icecream": 1500
}

# Meal Time Restrictions
meal_times = {
	"breakfast": (0, 7, 59),
	"lunch": (8, 15, 59),
	"dinner": (16, 23, 59)
}

# Allowed Channel ID (Replace with your channel ID)
ALLOWED_CHANNEL_ID = 1341113817668649091 # Replace with your desired channel ID

# Function: Check meal time validity
def can_feed(meal):
	now = datetime.datetime.now()
	start_hour, end_hour, end_minute = meal_times[meal]
	return start_hour <= now.hour <= end_hour and now.minute <= end_minute

# Function: Retrieve Pet Data
def get_pet(user_id):
	cursor.execute("SELECT * FROM pets WHERE user_id = ?", (user_id,))
	pet = cursor.fetchone()
	if not pet:
		cursor.execute("INSERT INTO pets (user_id) VALUES (?)", (user_id,))
		conn.commit()
		return get_pet(user_id) # Fetch newly created pet
	return pet

# Summon Pet
@bot.command()
async def summon(ctx):
	if ctx.channel.id != ALLOWED_CHANNEL_ID:
		return # Ignore commands outside allowed channel

	pet = get_pet(ctx.author.id)
	await ctx.send(f"🐷 **{pet[1]}** appears! Current weight: {pet[2]:.2f} lbs. Calories today: {pet[3]}/3000.")

# Feed Pet
@bot.command()
async def feed(ctx, meal: str, food: str):
	if ctx.channel.id != ALLOWED_CHANNEL_ID:
		return # Ignore commands outside allowed channel

	meal = meal.lower()
	food = food.lower()

	if meal not in meal_times:
		await ctx.send("❌ Invalid meal! Choose: breakfast, lunch, or dinner.")
		return

	if not can_feed(meal):
		await ctx.send(f"⏳ You can only feed **{meal}** during the set hours.")
		return

	if food not in food_options:
		await ctx.send("❌ Invalid food! Options: apple, hay, corn.")
		return

	pet = get_pet(ctx.author.id)

	if pet[3] >= 3000:
		await ctx.send("🐷 Your pet is full! No more meals today.")
		return

	new_calories = min(pet[3] + food_options[food], 3000)
	cursor.execute("UPDATE pets SET calories_today = ? WHERE user_id = ?", (new_calories, ctx.author.id))
	conn.commit()

	await ctx.send(f"🍽️ **{pet[1]}** ate **{food}**! Calories today: {new_calories}/3000.")

# Check Weight
@bot.command()
async def weight(ctx):
	if ctx.channel.id != ALLOWED_CHANNEL_ID:
		return # Ignore commands outside allowed channel

	pet = get_pet(ctx.author.id)
	await ctx.send(f"⚖️ **{pet[1]}** weighs **{pet[2]:.2f} lbs**.")

# Rename Pet
@bot.command()
async def rename(ctx, *, name: str):
	if ctx.channel.id != ALLOWED_CHANNEL_ID:
		return # Ignore commands outside allowed channel

	cursor.execute("UPDATE pets SET pet_name = ? WHERE user_id = ?", (name, ctx.author.id))
	conn.commit()
	await ctx.send(f"🐷 Your pet is now named **{name}**!")

# Daily Weight Update
@tasks.loop(hours=24)
async def update_weights():
	cursor.execute("SELECT user_id, weight, calories_today FROM pets")
	pets = cursor.fetchall()

	for pet in pets:
		user_id, weight, calories_today = pet
		net_calories = calories_today - 2000
		weight_change = net_calories / 3500
		new_weight = max(150, weight + weight_change)

		cursor.execute("UPDATE pets SET weight = ?, calories_today = 0 WHERE user_id = ?", (new_weight, user_id))

	conn.commit()

update_weights.start()

# Run the bot
bot.run("RAILWAY_TOKEN")