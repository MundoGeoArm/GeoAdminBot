import discord
from discord.ext import commands, tasks
from discord.ext import commands
from discord import app_commands
import json
import math
import asyncio
from keep_alive import keep_alive  # Mantener el bot activo en Replit
import datetime
import os
import re

keep_alive()  # Mantiene el bot activo

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.guild_messages = True
intents.message_content = True

# Leer el token desde una variable de entorno para mayor seguridad
TOKEN = os.getenv(
    "TOKEN_DISCORD"
)  # Asegúrate de que esta variable de entorno esté configurada en Replit

# Verificar si el token está cargado correctamente
if not TOKEN:
    print("Error: No se pudo cargar el token.")
    exit()

# Rutas de los archivos JSON
Ruta_Registro_Jugadores = "BaseDeDatos_Servidor/Registro_Jugadores.json"
Ruta_Registro_Paises = "BaseDeDatos_Servidor/Registro_Paises.json"
Ruta_Lista_Climas = "ListaAtributos/Lista_Climas.json"
Ruta_Lista_Continentes = "ListaAtributos/Lista_Continentes.json"
Ruta_Lista_Idiomas = "ListaAtributos/Lista_Idiomas.json"
Ruta_Lista_Religiones = "ListaAtributos/Lista_Religiones.json"


# Cargar la base de datos de jugadores (archivo JSON)
def cargar_jugadores():
    try:
        with open(Ruta_Registro_Jugadores, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Guardar la base de datos de jugadores
def guardar_jugadores(jugadores):
    with open(Ruta_Registro_Jugadores, 'w', encoding='utf-8') as f:
        json.dump(jugadores, f, indent=4, ensure_ascii=False)


# Prefijo de comandos
bot = commands.Bot(command_prefix='=', intents=intents)


@bot.event
async def on_ready():
    try:
        print(f'Bot conectado como {bot.user.name}')
        enviar_mensaje_periodico.start()
    except Exception as e:
        print(f"Error al conectar el bot: {str(e)}")


@tasks.loop(minutes=1)
async def enviar_mensaje_periodico():
    # Esperar hasta el próximo minuto
    now = datetime.datetime.now()
    seconds_until_next_minute = 60 - now.second
    await asyncio.sleep(seconds_until_next_minute)

    canal = bot.get_channel(1358714780034011298)
    if canal:
        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
        await canal.send(f"¡Mensaje automático! Hora: {hora_actual}")
    else:
        print("No se pudo encontrar el canal")


# Comando de registrar jugador (modificado para usar prefijo)
@bot.command(name="registrar-jugador",
             description="Registrar un jugador en la base de datos")
async def registrar_jugador(ctx,
                            user: discord.Member = None,
                            nombre: str = None,
                            rol: str = None):
    # Verificar que todos los argumentos estén presentes
    if user is None or nombre is None or rol is None:
        await ctx.send(
            "❌ **Error**: Faltan argumentos. Uso correcto:\n`=registrar-jugador @Usuario \"Nombre\" \"Rol\"`\n\nRecuerda:\n- Mencionar al usuario con @\n- Poner el nombre entre comillas\n- Poner el rol entre comillas"
        )
        return
    # Cargar los jugadores existentes
    jugadores = cargar_jugadores()

    # Generar un ID único para el jugador basado en el ID de Discord
    id_jugador = str(user.id)

    # Verificar si el jugador ya está registrado
    if id_jugador in jugadores:
        # Crear botones para confirmar o cancelar la modificación
        view = discord.ui.View()

        async def confirmar_callback(interaction: discord.Interaction):
            jugadores[id_jugador] = {
                "User": user.name,
                "Nombre": nombre,
                "Rol": rol
            }
            guardar_jugadores(jugadores)
            await interaction.response.send_message(
                f"Datos de {user.name} actualizados correctamente.")

        async def cancelar_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Operación cancelada.")

        # Añadir botones
        confirmar = discord.ui.Button(label="Confirmar",
                                      style=discord.ButtonStyle.green)
        cancelar = discord.ui.Button(label="Cancelar",
                                     style=discord.ButtonStyle.red)

        confirmar.callback = confirmar_callback
        cancelar.callback = cancelar_callback

        view.add_item(confirmar)
        view.add_item(cancelar)

        await ctx.send(
            f"¿Desea modificar los datos de {user.name} en la base de datos? Posiblemente este cambiando su Rol",
            view=view)
        return

    # Registrar el nuevo jugador
    jugadores[id_jugador] = {"User": user.name, "Nombre": nombre, "Rol": rol}

    # Guardar los cambios en el archivo JSON
    guardar_jugadores(jugadores)

    # Confirmar el registro
    await ctx.send(
        f"Jugador {user.name} registrado correctamente como {nombre} con el rol {rol}."
    )


# Función para crear el embed con los roles
def create_roles_embed(roles, page, per_page):
    start = page * per_page
    end = start + per_page
    roles_page = roles[start:end]

    # Enumerar roles con su rango correcto en la página
    roles_str = "\n".join([
        f"{start + i + 1}. {role.mention}" for i, role in enumerate(roles_page)
    ])

    embed = discord.Embed(title="**Roles en el servidor**",
                          description=roles_str,
                          color=discord.Color.blue())
    total_pages = math.ceil(len(roles) / per_page)
    embed.set_footer(
        text=
        f"Página {page + 1} de {total_pages} | Roles {start + 1}-{min(end, len(roles))} | Total roles {len(roles)}"
    )
    return embed


# Comando para listar roles
@bot.command(name="listar-roles")
async def listar_roles(ctx, pagina: int = 1):
    try:
        # Obtener roles y mantener el orden del servidor (excluyendo @everyone)
        roles = list(reversed(ctx.guild.roles))[:-1]

        # Calcular el número total de páginas
        per_page = 40
        total_pages = math.ceil(len(roles) / per_page)

        # Verificar que la página solicitada esté dentro del rango
        if pagina < 1 or pagina > total_pages:
            await ctx.send(
                f"Por favor, ingrese una página válida (de 1 a {total_pages})."
            )
            return

        # Crear el embed con los roles de la página solicitada
        embed = create_roles_embed(roles, pagina - 1, per_page)

        # Crear vista con botones de navegación
        async def create_view(current_page):
            view = discord.ui.View()

            # Botón anterior
            anterior = discord.ui.Button(label="◀️",
                                         style=discord.ButtonStyle.gray,
                                         disabled=current_page <= 1)

            async def anterior_callback(interaction: discord.Interaction):
                new_page = current_page - 1
                new_view = await create_view(new_page)
                await interaction.response.edit_message(
                    embed=create_roles_embed(roles, new_page - 1, per_page),
                    view=new_view)

            anterior.callback = anterior_callback

            # Botón siguiente
            siguiente = discord.ui.Button(label="▶️",
                                          style=discord.ButtonStyle.gray,
                                          disabled=current_page >= total_pages)

            async def siguiente_callback(interaction: discord.Interaction):
                new_page = current_page + 1
                new_view = await create_view(new_page)
                await interaction.response.edit_message(
                    embed=create_roles_embed(roles, new_page - 1, per_page),
                    view=new_view)

            siguiente.callback = siguiente_callback

            view.add_item(anterior)
            view.add_item(siguiente)
            return view

        # Crear vista inicial
        view = await create_view(pagina)

        # Enviar el embed con los roles y botones
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"Ocurrió un error al listar los roles: {str(e)}")


# Comando para borrar canales no categorizados
@bot.command(name='borrar-canales-no-categorizados')
@commands.has_permissions(administrator=True)
async def limpiar_canales(ctx):
    """Elimina todos los canales que no estén en una categoría, excepto uno llamado 'moderator-only'."""
    guild = ctx.guild
    contador = 0

    for canal in guild.channels:
        if isinstance(canal, discord.TextChannel):
            # Verificamos que no tenga categoría y que no sea el canal protegido
            if canal.category is None and canal.name != 'moderator-only':
                try:
                    await canal.delete()
                    contador += 1
                except discord.Forbidden:
                    await ctx.send(
                        f"No tengo permisos para borrar el canal: {canal.name}"
                    )
                except Exception as e:
                    await ctx.send(f"Error al borrar {canal.name}: {str(e)}")

    await ctx.send(f"Se eliminaron {contador} canales no categorizados.")


# Manejo global de errores
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"❌ **Error**: Falta el argumento `{error.param.name}`. Usa `=help {ctx.command.name}` para ver cómo usar el comando."
        )
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(
            "❌ **Error**: No se encontró al usuario mencionado. Asegúrate de mencionar a un usuario válido con @."
        )
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ **Error**: No tienes los permisos necesarios para usar este comando."
        )
    else:
        await ctx.send(f"❌ **Error inesperado**: {str(error)}")


# Manejo de errores específicos
@limpiar_canales.error
async def limpiar_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "No tienes permisos de administrador para usar este comando.")
    else:
        await ctx.send(f"Error: {str(error)}")


# Comando para borrar canal(s)
@bot.command(name='borrar-canal')
async def borrar_canal(ctx, *canales: discord.TextChannel):
    if not canales:
        await ctx.send("Debes mencionar al menos un canal para borrar.")
        return

    eliminados = []
    fallidos = []

    for canal in canales:
        try:
            await canal.delete()
            eliminados.append(canal.name)
        except Exception as e:
            fallidos.append((canal.name, str(e)))

    mensaje = ""
    if eliminados:
        mensaje += f"Canales eliminados correctamente: {', '.join(eliminados)}\n"
    if fallidos:
        mensaje += "Errores al eliminar:\n"
        for nombre, error in fallidos:
            mensaje += f"- {nombre}: {error}\n"

    await ctx.send(mensaje)


# Comando para crear país
@bot.command(name='crear-pais')
async def crear_pais(ctx, nombre: str):
    try:
        # Cargar países existentes
        with open(Ruta_Registro_Paises, 'r', encoding='utf-8') as f:
            paises = json.load(f)

        # Verificar si el país ya existe
        if nombre in paises:
            await ctx.send(
                f"❌ El país {nombre} ya existe en la base de datos. Solo se puede editar."
            )
            return

        # Crear estructura del nuevo país
        paises[nombre] = {
            "última carga datos": "No-registrado",
            "último cálculo": "No-registrado",
            "CAPITAL": "No-registrado",
            "TERRITORIO_KM2": 0,
            "CONTINENTES": [],
            "CLIMAS": [],
            "HABITANTES": {
                "nacionales": 0,
                "extranjeros": 0
            },
            "IDIOMAS": [],
            "RELIGIONES": [],
            "RECURSOS_NATURALES": {
                "REC-MAD": 10000,
                "REC-CON": 10000,
                "REC-HIE": 10000,
                "REC-ALU": 10000,
                "REC-COB": 10000,
                "REC-PLO": 10000,
                "REC-ORO": 10000,
                "REC-TIT": 10000,
                "REC-LIT": 10000,
                "REC-URA": 10000,
                "REC-PET": 10000,
                "REC-GAS": 10000,
                "REC-AGU": 10000
            },
            "INVENTARIO": {}
        }

        # Guardar cambios
        with open(Ruta_Registro_Paises, 'w', encoding='utf-8') as f:
            json.dump(paises, f, indent=4, ensure_ascii=False)

        await ctx.send(f"✅ País {nombre} creado exitosamente.")

    except Exception as e:
        await ctx.send(f"❌ Error al crear el país: {str(e)}")


# Comando para ver datos de país
@bot.command(name='datos-pais')
async def datos_pais(ctx, usuario: discord.Member):
    try:
        # Cargar datos necesarios
        with open(Ruta_Registro_Jugadores, 'r', encoding='utf-8') as f:
            jugadores = json.load(f)
        with open(Ruta_Registro_Paises, 'r', encoding='utf-8') as f:
            paises = json.load(f)
        with open(Ruta_Lista_Continentes, 'r', encoding='utf-8') as f:
            continentes = json.load(f)
        with open(Ruta_Lista_Climas, 'r', encoding='utf-8') as f:
            climas = json.load(f)
        with open(Ruta_Lista_Idiomas, 'r', encoding='utf-8') as f:
            idiomas = json.load(f)
        with open(Ruta_Lista_Religiones, 'r', encoding='utf-8') as f:
            religiones = json.load(f)

        # Obtener el país del usuario
        usuario_id = str(usuario.id)
        if usuario_id not in jugadores:
            await ctx.send(
                "❌ El usuario no está registrado en la base de datos.")
            return

        pais_nombre = jugadores[usuario_id]["Rol"]
        if pais_nombre not in paises:
            await ctx.send(
                "❌ El país del usuario no existe en la base de datos.")
            return

        pais_data = paises[pais_nombre]

        # Crear embed
        embed = discord.Embed(title=f"Datos de {pais_nombre}",
                              color=discord.Color.blue())
        embed.add_field(name="PRESIDENTE", value=usuario.mention, inline=False)
        embed.add_field(name="CAPITAL",
                        value=pais_data["CAPITAL"],
                        inline=True)
        embed.add_field(name="TERRITORIO",
                        value=f"{pais_data['TERRITORIO_KM2']} km²",
                        inline=True)

        # Mostrar nombres en lugar de menciones si los roles no existen
        continentes_str = ", ".join(pais_data["CONTINENTES"]) or "Ninguno"
        climas_str = ", ".join(pais_data["CLIMAS"]) or "Ninguno"
        idiomas_str = ", ".join(pais_data["IDIOMAS"]) or "Ninguno"
        religiones_str = ", ".join(pais_data["RELIGIONES"]) or "Ninguno"

        embed.add_field(name="CONTINENTES",
                        value=continentes_str,
                        inline=False)
        embed.add_field(name="CLIMAS", value=climas_str, inline=False)
        embed.add_field(
            name="HABITANTES",
            value=
            f"📊 {pais_data['HABITANTES']['nacionales']} Nacionales | {pais_data['HABITANTES']['extranjeros']} Extranjeros",
            inline=False)
        embed.add_field(name="IDIOMAS", value=idiomas_str, inline=False)
        embed.add_field(name="RELIGIONES", value=religiones_str, inline=False)

        # Recursos naturales
        recursos_str = "\n".join([
            f"{rec}: {cant:,}"
            for rec, cant in pais_data["RECURSOS_NATURALES"].items()
        ])
        embed.add_field(name="RECURSOS NATURALES",
                        value=f"```\n{recursos_str}\n```",
                        inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error al mostrar datos del país: {str(e)}")


# Comando para crear un rol individual
@bot.command(name='crear-rol')
async def crear_rol(ctx,
                    nombre: str,
                    color: str,
                    rol_base: discord.Role = None):
    try:
        # Convertir el color hexadecimal a un objeto Color
        color_hex = int(color.strip('#'), 16)

        # Crear el rol nuevo
        nuevo_rol = await ctx.guild.create_role(name=nombre,
                                                color=discord.Color(color_hex))

        # Si se especificó un rol base, mover el nuevo rol encima de él
        if rol_base:
            await nuevo_rol.edit(position=rol_base.position + 1)

        await ctx.send(f"✅ Rol {nuevo_rol.mention} creado exitosamente.")

    except ValueError:
        await ctx.send(
            "❌ El color debe ser un valor hexadecimal válido (ejemplo: 39D600)"
        )
    except Exception as e:
        await ctx.send(f"❌ Error al crear el rol: {str(e)}")


# Comando para crear múltiples roles desde un archivo
@bot.command(name='crear-roles')
async def crear_roles_archivo(ctx,
                              archivo: str,
                              color: str,
                              rol_base: discord.Role = None):
    try:
        # Verificar que el archivo exista y tenga extensión .txt
        if not archivo.endswith('.txt'):
            await ctx.send("❌ El archivo debe tener extensión .txt")
            return

        # Convertir el color hexadecimal
        color_hex = int(color.strip('#'), 16)

        # Leer el archivo
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                nombres_roles = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            await ctx.send(f"❌ No se encontró el archivo {archivo}")
            return

        # Crear los roles
        roles_creados = []
        posicion_base = rol_base.position if rol_base else 0

        for i, nombre in enumerate(nombres_roles):
            nuevo_rol = await ctx.guild.create_role(
                name=nombre, color=discord.Color(color_hex))
            if rol_base:
                await nuevo_rol.edit(position=posicion_base + 1 + i)
            roles_creados.append(nuevo_rol.mention)

        # Mostrar resumen
        roles_str = "\n".join(roles_creados)
        await ctx.send(f"✅ Roles creados exitosamente:\n{roles_str}")

    except ValueError:
        await ctx.send(
            "❌ El color debe ser un valor hexadecimal válido (ejemplo: 39D600)"
        )
    except Exception as e:
        await ctx.send(f"❌ Error al crear los roles: {str(e)}")


@bot.command(name="mover-rol")
async def mover_rol(ctx, rol_a_mover: discord.Role, destino_rol: discord.Role):
    try:
        # Asegurarse de que el autor tiene permisos para mover roles
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("No tienes permisos para mover roles.")
            return

        # Mover el rol justo encima del rol de destino
        # Utilizamos la posición exacta del rol de destino
        await rol_a_mover.edit(position=destino_rol.position + 1)

        await ctx.send(
            f"**El rol {rol_a_mover.name} ha sido movido encima de {destino_rol.name}.**"
        )

        # Esperar un breve momento para asegurar que la sincronización de roles se haya completado
        await asyncio.sleep(1)

        # Obtener los roles actualizados
        roles = ctx.guild.roles[1:]  # Excluir el rol @everyone
        roles = sorted(roles, key=lambda role: role.position,
                       reverse=True)  # Ordenar roles de mayor a menor

        # Calcular la página donde está el rol movido
        per_page = 40
        total_pages = math.ceil(len(roles) / per_page)

        # Buscar el índice del rol movido en la lista
        index_rol_moved = roles.index(rol_a_mover)

        # Calcular la página en la que se encuentra
        page = index_rol_moved // per_page + 1  # +1 porque la página empieza desde 1

        # Ejecutar y mostrar el embed de la página correspondiente
        await listar_roles(ctx, page)

    except Exception as e:
        await ctx.send(f"Ocurrió un error al mover el rol: {str(e)}")


@bot.command(name='mover-roles')
async def mover_roles(ctx, rol_inicio: discord.Role, rol_fin: discord.Role,
                      rol_destino: discord.Role):
    try:
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("No tienes permisos para mover roles.")
            return

        # Ordenar todos los roles de menor a mayor (posición baja a alta)
        roles = sorted(ctx.guild.roles, key=lambda r: r.position)

        # Obtener posiciones actuales de los roles involucrados
        inicio_pos = roles.index(rol_inicio)
        fin_pos = roles.index(rol_fin)
        destino_pos = roles.index(rol_destino)

        # Asegurar orden
        if inicio_pos > fin_pos:
            inicio_pos, fin_pos = fin_pos, inicio_pos

        # Extraer los roles a mover
        roles_a_mover = roles[inicio_pos:fin_pos + 1]

        # Eliminar esos roles de la jerarquía
        roles_sin_mover = [r for r in roles if r not in roles_a_mover]

        # Insertarlos encima del rol destino
        insert_index = roles_sin_mover.index(rol_destino) + 1
        nueva_jerarquia = (roles_sin_mover[:insert_index] + roles_a_mover +
                           roles_sin_mover[insert_index:])

        # Reasignar posiciones uno por uno (posición = índice)
        for i, rol in enumerate(nueva_jerarquia):
            if rol.position != i:
                await rol.edit(position=i)
                await asyncio.sleep(
                    0.2)  # Espera breve para evitar conflictos con Discord

        await ctx.send(
            f"✅ Se han reordenado {len(roles_a_mover)} roles encima de {rol_destino.mention} con precisión total."
        )

    except Exception as e:
        await ctx.send(f"❌ Error al mover los roles: {str(e)}")


# Comando para borrar rol(s)
@bot.command(name='borrar-rol')
async def borrar_rol(ctx, *roles: discord.Role):
    if not roles:
        await ctx.send("Debes mencionar al menos un rol para borrar.")
        return

    eliminados = []
    fallidos = []

    for rol in roles:
        try:
            await rol.delete()
            eliminados.append(rol.name)
        except Exception as e:
            fallidos.append((rol.name, str(e)))

    mensaje = ""
    if eliminados:
        mensaje += f"Roles eliminados correctamente: {', '.join(eliminados)}\n"
    if fallidos:
        mensaje += "Errores al eliminar:\n"
        for nombre, error in fallidos:
            mensaje += f"- {nombre}: {error}\n"

    await ctx.send(mensaje)











# Variables globales
inventory_message_id = None
inventory_bot_id = None  # Guardará el ID del bot de Unbelieva que se utilizará
inventory_data = []  # Para almacenar la información extraída

def extract_inventory_info(content):
    items = []
    lines = content.splitlines()  # Divide el contenido en líneas
    for line in lines:
        line = line.strip()  # Elimina espacios adicionales
        if line:  # Asegura que la línea no esté vacía
            words = line.split()  # Divide la línea en palabras
            if len(words) > 1:  # Verifica que haya al menos una palabra (evitar líneas vacías)
                cantidad = words[0]  # Primer palabra es la cantidad
                clave = words[-1]    # Última palabra es la clave
                items.append((cantidad, clave))  # Añadir a la lista
                print(f"Procesando línea: {line}")  # Para ver cómo se procesa cada línea
                print(f"Cantidad: {cantidad}, Clave: {clave}")
    return items


# Comando para localizar un bot de Unbelieva
@bot.command(name='bot-unbelieva')
async def bot_unbelieva(ctx, bot_user: discord.User):
    """Comando para localizar el bot de Unbelieva"""
    global inventory_bot_id
    # Guardamos el ID del bot para usarlo después
    inventory_bot_id = bot_user.id
    await ctx.send(f'Bot de Unbelieva localizado: {bot_user.name}')


# Comando para leer el inventario de un usuario
@bot.command(name='leer-inventario-unbelieva')
async def leer_inventario_unbelieva(ctx, user: discord.Member):
    global inventory_message_id, inventory_data

    # Verificar si se ha configurado el bot de Unbelieva
    if inventory_bot_id is None:
        await ctx.send("No se ha configurado un bot de Unbelieva. Usa =bot-unbelieva @el_bot para configurarlo.")
        return

    inventory_data.clear()  # Limpiar cualquier dato anterior

    # Buscar el mensaje del bot de Unbelieva después de que el usuario use +inv
    def check(message):
        return message.author.id == inventory_bot_id and message.channel == ctx.channel

    await ctx.send(f"Buscando inventario de {user.mention}...")

    try:
        # Esperar el mensaje del bot de Unbelieva
        message = await bot.wait_for('message', check=check, timeout=60)
        inventory_message_id = message.id

        # Extraer información del embed
        embed_content = ""
        for embed in message.embeds:
            embed_content += embed.description or ""
            for field in embed.fields:
                embed_content += f"{field.name}: {field.value}"

        # Extraer la cantidad y clave usando la función
        inventory_data = extract_inventory_info(embed_content)

        await ctx.send(f"Inventario de {user.mention} extraído correctamente.")
    except Exception as e:
        await ctx.send(f"Error: No se pudo encontrar el inventario del usuario. Detalles: {str(e)}")

# Comando para mostrar los datos extraídos del inventario
@bot.command(name='mostrar-inventario')
async def mostrar_inventario(ctx):
    if not inventory_data:
        await ctx.send("No se ha extraído ningún inventario aún.")
    else:
        # Mostrar la información extraída
        data_message = "\n".join([f"{cantidad} - {clave}" for cantidad, clave in inventory_data])
        await ctx.send(f"Inventario extraído:\n{data_message}")


# Ejecutar el bot con el token
bot.run(TOKEN)








