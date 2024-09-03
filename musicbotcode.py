import discord
import yt_dlp as youtube_dl
import asyncio
import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials

# Configuración de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="", client_secret=""))

# Configuración del bot de Discord
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True
}

# Cola de reproducción
queue = []

def get_spotify_tracks(playlist_url):
    # Extraer el ID de la lista de reproducción
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    results = sp.playlist_tracks(playlist_id)
    tracks = []
    for item in results['items']:
        track = item['track']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        search_query = f"{artist_name} {track_name}"
        tracks.append(search_query)
    return tracks

async def play_next(ctx):
    if queue:
        track = queue.pop(0)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{track}", download=False)
                url = info['entries'][0]['url']
                audio_source = discord.FFmpegPCMAudio(url)

                voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
                if voice:
                    voice.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))

                await ctx.send(f"Reproduciendo: {track}")

            except Exception as e:
                await ctx.send(f"No se pudo reproducir {track}: {str(e)}")
                await play_next(ctx)  # Intenta reproducir la siguiente canción en caso de error

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel:
        # El bot se ha unido a un canal de voz
        channel = after.channel
        await channel.send(
            "Hola flaco estoy aca para que no tengas que bancarte a los boludos de discord. "
            "Aca están los comandos que podes usar:\n"
            "`!play [URL]`: Para empezar a reproducir una lista de reproducción de Spotify.\n"
            "`!skip`: Para saltar la canción actual.\n"
            "`!pause`: Para pausar la canción actual.\n"
            "`!resume`: Para reanudar la canción actual.\n"
            "`!desconectar`: Para que el bot se desconecte del canal de voz.\n"
        )

@bot.command()
async def play(ctx, playlist_url: str):
    # Validar el URL de Spotify
    if not playlist_url.startswith("https://open.spotify.com/playlist/"):
        await ctx.send("El URL proporcionado no es una lista de reproducción de Spotify válida.")
        return

    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("¡Debes estar en un canal de voz para reproducir música!")
        return

    # Conectar al canal de voz si no está conectado
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice:
        voice = await voice_channel.connect()

    tracks = get_spotify_tracks(playlist_url)
    queue.extend(tracks)

    if not voice.is_playing():
        await play_next(ctx)

@bot.command()
async def skip(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("Canción saltada.")
    else:
        await ctx.send("No hay ninguna canción reproduciéndose.")

@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("Canción pausada.")
    else:
        await ctx.send("No hay ninguna canción reproduciéndose.")

@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("Canción reanudada.")
    else:
        await ctx.send("No hay ninguna canción pausada.")

@bot.command()
async def desconectar(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send("Desconectado del canal de voz.")
    else:
        await ctx.send("El bot no está conectado a un canal de voz.")

bot.run('')
