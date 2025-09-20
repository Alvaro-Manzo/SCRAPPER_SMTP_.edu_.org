import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import sys
import time
import random
import os
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ScrapperConsola:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.universidades = [
            'https://www.harvard.edu',
            'https://www.mit.edu', 
            'https://www.stanford.edu',
            'https://www.berkeley.edu',
            'https://www.yale.edu',
            'https://www.princeton.edu',
            'https://www.columbia.edu',
            'https://www.cornell.edu',
            'https://www.upenn.edu',
            'https://www.caltech.edu'
        ]
        
        self.organizaciones = [
            'https://www.redcross.org',
            'https://www.unicef.org',
            'https://www.who.int',
            'https://www.amnesty.org',
            'https://www.greenpeace.org',
            'https://www.oxfam.org',
            'https://www.savethechildren.org'
        ]
        
        # Crear directorio de resultados
        self.results_dir = "resultados_scrapping"
        os.makedirs(self.results_dir, exist_ok=True)

    def extraer_emails_edu_org(self, texto):
        """Extrae solo correos que terminen en .edu o .org"""
        patron = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(edu|org)"
        emails_completos = set()
        for match in re.finditer(patron, texto, re.IGNORECASE):
            emails_completos.add(match.group(0).lower())
        return emails_completos

    def crear_session_protegida(self):
        """Crea sesión HTTP con protecciones"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        session.headers.update(headers)
        return session

    def guardar_resultados(self, emails, nombre_archivo, info_busqueda):
        """Guarda los resultados en correos.txt con numeración consecutiva"""
        archivo_principal = os.path.join(self.results_dir, "correos.txt")
        
        # Leer el archivo existente para mantener la numeración consecutiva
        emails_existentes = []
        if os.path.exists(archivo_principal):
            try:
                with open(archivo_principal, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    # Extraer correos existentes para evitar duplicados
                    for linea in contenido.split('\n'):
                        if '. ' in linea and '@' in linea:
                            email = linea.split('. ', 1)[1].strip()
                            if email and email not in emails_existentes:
                                emails_existentes.append(email)
            except:
                emails_existentes = []
        
        # Filtrar correos nuevos (no duplicados)
        emails_nuevos = []
        for email in sorted(emails):
            if email not in emails_existentes:
                emails_nuevos.append(email)
        
        # Escribir al archivo principal
        with open(archivo_principal, 'a', encoding='utf-8') as f:
            # Si es la primera vez, escribir encabezado
            if not emails_existentes:
                f.write("="*70 + "\n")
                f.write("🤖 SCRAPPER PRO - TODOS LOS CORREOS ENCONTRADOS\n")
                f.write("="*70 + "\n\n")
            
            # Agregar nueva búsqueda
            f.write(f"\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {info_busqueda.get('tipo', 'Búsqueda')}\n")
            f.write(f"🌐 Fuente: {info_busqueda.get('fuente', 'Múltiples')}\n")
            f.write(f"📧 Correos nuevos encontrados: {len(emails_nuevos)}\n")
            f.write("-" * 50 + "\n")
            
            if emails_nuevos:
                # Continuar numeración desde donde se quedó
                numero_inicial = len(emails_existentes) + 1
                for i, email in enumerate(emails_nuevos):
                    f.write(f"{numero_inicial + i:4d}. {email}\n")
            else:
                f.write("(No se encontraron correos nuevos)\n")
            
            f.write("\n")
        
        return archivo_principal

    def es_url_valida(self, url, dominio):
        """Verifica si la URL pertenece al dominio especificado"""
        try:
            return urlparse(url).netloc.endswith(dominio)
        except:
            return False

    def obtener_urls(self, html, base_url, dominio):
        """Extrae URLs válidas de la página HTML"""
        soup = BeautifulSoup(html, "html.parser")
        urls = set()
        for enlace in soup.find_all("a", href=True):
            try:
                url = urljoin(base_url, enlace["href"])
                if self.es_url_valida(url, dominio) and url.startswith(('http://', 'https://')):
                    urls.add(url)
            except:
                continue
        return urls

    def scrapear_sitio(self, url_inicial, max_paginas=30):
        """Función principal para scrapear un sitio completo"""
        print(f"\n{'='*70}")
        print("🤖 SCRAPPER PRO - BÚSQUEDA EN SITIO ESPECÍFICO")
        print(f"{'='*70}")
        
        dominio_raiz = urlparse(url_inicial).netloc
        visitados = set()
        pendientes = set([url_inicial])
        encontrados = set()

        print(f"🌐 Sitio objetivo: {dominio_raiz}")
        print(f"📄 Límite de páginas: {max_paginas}")
        print(f"🔍 Buscando correos .edu/.org...")
        print("-" * 50)
        
        session = self.crear_session_protegida()
        inicio = time.time()

        while pendientes and len(visitados) < max_paginas:
            url_actual = pendientes.pop()
            if url_actual in visitados:
                continue
                
            print(f"📄 Página {len(visitados)+1:2d}/{max_paginas}: {url_actual[:60]}...")
            
            try:
                # Pausa anti-detección
                time.sleep(random.uniform(1, 3))
                
                resp = session.get(url_actual, timeout=15)
                resp.raise_for_status()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}...")
                visitados.add(url_actual)
                continue

            # Buscar correos .edu/.org
            emails = self.extraer_emails_edu_org(resp.text)
            nuevos_emails = emails - encontrados
            
            if nuevos_emails:
                print(f"   ✅ {len(nuevos_emails)} nuevos correos encontrados!")
                for email in list(nuevos_emails)[:3]:  # Mostrar máximo 3
                    print(f"      📧 {email}")
                if len(nuevos_emails) > 3:
                    print(f"      ... y {len(nuevos_emails) - 3} más")
            
            encontrados.update(emails)
            
            # Obtener nuevas URLs
            try:
                nuevos = self.obtener_urls(resp.text, url_actual, dominio_raiz)
                pendientes.update(nuevos - visitados)
            except:
                pass
                
            visitados.add(url_actual)

        tiempo_total = time.time() - inicio
        
        # Mostrar resultados finales
        print(f"\n{'='*70}")
        print("📊 RESULTADOS FINALES")
        print(f"{'='*70}")
        
        if encontrados:
            print(f"✅ {len(encontrados)} correos .edu/.org encontrados")
            print(f"🌐 {len(visitados)} páginas procesadas")
            print(f"⏱️ Tiempo total: {tiempo_total:.1f} segundos")
            
            # Guardar archivo
            info = {
                'tipo': 'Sitio Específico',
                'fuente': url_inicial,
                'paginas': len(visitados),
                'tiempo': f"{tiempo_total:.1f} segundos"
            }
            
            archivo = self.guardar_resultados(encontrados, "sitio_especifico", info)
            print(f"📁 Archivo guardado: {archivo}")
            
            # Mostrar muestra de correos
            print(f"\n📋 MUESTRA DE CORREOS (primeros 10):")
            for i, email in enumerate(sorted(encontrados)[:10], 1):
                print(f"   {i:2d}. {email}")
            
            if len(encontrados) > 10:
                print(f"   ... y {len(encontrados) - 10} más en el archivo")
                
        else:
            print("❌ No se encontraron correos .edu/.org")
            print(f"🌐 {len(visitados)} páginas procesadas")
            print(f"⏱️ Tiempo total: {tiempo_total:.1f} segundos")
            
            print("\n💡 Posibles razones:")
            print("   • El sitio no tiene correos públicos")
            print("   • Los correos requieren JavaScript")
            print("   • El sitio bloquea bots")
        
        return encontrados

    def buscar_en_lista_sitios(self, urls, nombre_categoria, nombre_archivo):
        """Busca correos en una lista de URLs"""
        print(f"\n{'='*70}")
        print(f"🤖 SCRAPPER PRO - {nombre_categoria.upper()}")
        print(f"{'='*70}")
        
        todos_los_emails = set()
        inicio = time.time()
        
        print(f"🎯 Analizando {len(urls)} sitios...")
        print(f"🔍 Buscando correos .edu/.org...")
        print("-" * 50)
        
        for i, url in enumerate(urls, 1):
            print(f"\n📍 Sitio {i}/{len(urls)}: {url}")
            
            try:
                session = self.crear_session_protegida()
                delay = random.uniform(2, 5)
                print(f"   ⏳ Esperando {delay:.1f}s...")
                time.sleep(delay)
                
                resp = session.get(url, timeout=15)
                resp.raise_for_status()
                
                emails = self.extraer_emails_edu_org(resp.text)
                nuevos_emails = emails - todos_los_emails
                
                if nuevos_emails:
                    print(f"   ✅ {len(nuevos_emails)} nuevos correos encontrados:")
                    for email in list(nuevos_emails)[:3]:
                        print(f"      📧 {email}")
                    if len(nuevos_emails) > 3:
                        print(f"      ... y {len(nuevos_emails) - 3} más")
                else:
                    print(f"   ❌ No se encontraron correos nuevos")
                
                todos_los_emails.update(emails)
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}...")
                continue
        
        tiempo_total = time.time() - inicio
        
        # Mostrar resultados finales
        print(f"\n{'='*70}")
        print("📊 RESULTADOS FINALES")
        print(f"{'='*70}")
        
        if todos_los_emails:
            print(f"✅ {len(todos_los_emails)} correos únicos encontrados")
            print(f"🌐 {len(urls)} sitios procesados")
            print(f"⏱️ Tiempo total: {tiempo_total:.1f} segundos")
            
            # Guardar archivo
            info = {
                'tipo': nombre_categoria,
                'fuente': f"{len(urls)} sitios web",
                'paginas': len(urls),
                'tiempo': f"{tiempo_total:.1f} segundos"
            }
            
            archivo = self.guardar_resultados(todos_los_emails, nombre_archivo, info)
            print(f"📁 Archivo guardado: {archivo}")
            
            # Mostrar todos los correos
            print(f"\n📋 TODOS LOS CORREOS ENCONTRADOS:")
            for i, email in enumerate(sorted(todos_los_emails), 1):
                print(f"   {i:3d}. {email}")
                
        else:
            print("❌ No se encontraron correos .edu/.org")
            print(f"🌐 {len(urls)} sitios procesados")
            print(f"⏱️ Tiempo total: {tiempo_total:.1f} segundos")
        
        return todos_los_emails

    def mostrar_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*70)
        print("🤖 SCRAPPER PRO - VERSIÓN CONSOLA")
        print("="*70)
        print("1. 🌐 Scrapear sitio específico completo")
        print("2. 🎓 Buscar en universidades famosas")
        print("3. 🏢 Buscar en organizaciones")
        print("4. 🔍 Buscar en TODAS las fuentes")
        print("5. 🎯 Mostrar Google Dorks")
        print("6. 📁 Ver archivos generados")
        print("7. 🛡️ Información sobre privacidad")
        print("8. ❓ Ayuda y consejos")
        print("0. ❌ Salir")
        print("="*70)

    def mostrar_google_dorks(self):
        """Muestra Google Dorks útiles"""
        print(f"\n{'='*70}")
        print("🎯 GOOGLE DORKS PARA CORREOS .EDU/.ORG")
        print(f"{'='*70}")
        
        dorks = [
            'site:.edu "email" OR "mail" OR "@"',
            'site:.org "contact" OR "@"',
            'site:.edu filetype:pdf "@"',
            'site:.org "staff directory"',
            'site:.edu "faculty" "@"',
            'site:.org "board members"',
            'intext:"@*.edu" -inurl:login',
            'intext:"@*.org" -inurl:login',
            'site:.edu "department" contact',
            'site:.org "team" OR "staff"'
        ]
        
        print("\n💡 Copia y pega estos comandos en Google:")
        print("-" * 50)
        for i, dork in enumerate(dorks, 1):
            print(f"{i:2d}. {dork}")
        
        print(f"\n📝 CONSEJOS ADICIONALES:")
        print("• Reemplaza términos por 'directory', 'staff', 'faculty'")
        print("• Usa comillas para búsquedas exactas")
        print("• Combina con nombres de universidades específicas")
        print("• Prueba con 'professor', 'administrator', 'researcher'")

    def ver_archivos_generados(self):
        """Muestra los archivos generados"""
        print(f"\n{'='*70}")
        print("📁 ARCHIVOS GENERADOS")
        print(f"{'='*70}")
        
        try:
            archivos = [f for f in os.listdir(self.results_dir) if f.endswith('.txt')]
            archivos.sort(reverse=True)  # Más recientes primero
            
            if archivos:
                print(f"\n📂 Directorio: {self.results_dir}")
                print(f"📊 Total de archivos: {len(archivos)}")
                print("-" * 50)
                
                for i, archivo in enumerate(archivos[:10], 1):  # Mostrar últimos 10
                    ruta_completa = os.path.join(self.results_dir, archivo)
                    size = os.path.getsize(ruta_completa)
                    fecha = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                    
                    print(f"{i:2d}. {archivo}")
                    print(f"    📅 {fecha.strftime('%d/%m/%Y %H:%M:%S')}")
                    print(f"    📦 {size:,} bytes")
                    print()
                
                if len(archivos) > 10:
                    print(f"... y {len(archivos) - 10} archivos más")
                    
                print(f"🌍 Ubicación completa: {os.path.abspath(self.results_dir)}")
            else:
                print("\n❌ No se han generado archivos aún")
                print("💡 Ejecuta alguna búsqueda para generar archivos")
        
        except Exception as e:
            print(f"\n❌ Error accediendo a archivos: {str(e)}")

    def mostrar_info_privacidad(self):
        """Información sobre privacidad"""
        print(f"\n{'='*70}")
        print("🛡️ INFORMACIÓN SOBRE PRIVACIDAD Y SEGURIDAD")
        print(f"{'='*70}")
        print("""
❗ ¿SE VE MI IP CUANDO HAGO SCRAPING?
SÍ, cuando haces scraping, los servidores web pueden ver:
• Tu dirección IP real
• Timestamp de cada petición  
• Tu User-Agent (navegador simulado)
• Todas las páginas que visitas

🔒 PROTECCIONES IMPLEMENTADAS EN ESTE SCRAPPER:
✅ Rotación aleatoria de User-Agents
✅ Delays aleatorios entre peticiones (1-3 segundos)
✅ Headers realistas de navegador
✅ Manejo de errores y reintentos
✅ Límites de páginas por búsqueda

🛡️ CÓMO MEJORAR TU ANONIMATO:
1. 🌐 VPN (MÁS RECOMENDADO):
   • NordVPN, ExpressVPN, ProtonVPN
   • Oculta completamente tu IP
   • Más seguro que proxies gratuitos

2. 🔗 Proxies:
   • Configurables en el código
   • Busca proxies en free-proxy-list.net
   • Ten cuidado con proxies maliciosos

3. 🕷️ Red Tor:
   • Anonimato máximo pero muy lento
   • Algunos sitios lo bloquean

4. 📱 Cambiar de red:
   • Usar datos móviles
   • Conectarse desde diferentes ubicaciones

⚖️ CONSIDERACIONES LEGALES:
• Lee siempre robots.txt de cada sitio
• Respeta términos de servicio
• No sobrecargues servidores
• Usa solo para propósitos legítimos
• Algunos países tienen leyes específicas sobre scraping
""")

    def mostrar_ayuda(self):
        """Muestra ayuda y consejos"""
        print(f"\n{'='*70}")
        print("❓ AYUDA Y CONSEJOS PARA USAR EL SCRAPPER")
        print(f"{'='*70}")
        print("""
🤖 ¿QUÉ HACE ESTE SCRAPPER?
• Busca correos electrónicos que terminen en .edu y .org
• Analiza sitios web de universidades y organizaciones
• Exporta resultados automáticamente a archivos .txt
• Incluye protecciones anti-detección

🎯 MEJORES ESTRATEGIAS:
1. 🎓 Para Universidades (.edu):
   • Busca en páginas de facultad/directorio
   • Analiza departamentos académicos
   • Revisa páginas de cursos y profesores
   • Eventos académicos y conferencias

2. 🏢 Para Organizaciones (.org):
   • Páginas "About us" / "Our team"
   • Directorios de staff
   • Informes anuales (si están en HTML)
   • Páginas de contacto por departamento

🔍 CONSEJOS PARA BÚSQUEDAS EXITOSAS:
• Empieza con sitios grandes y conocidos
• Los sitios .edu/.org tienden a tener más correos públicos
• Algunos sitios requieren JavaScript (no detectables)
• Las universidades pequeñas a veces tienen más correos visibles
• Evita sitios que requieren login

📁 ARCHIVOS GENERADOS:
• Se guardan automáticamente en la carpeta 'resultados_scrapping'
• Incluyen timestamp y estadísticas detalladas
• Formato .txt fácil de abrir en cualquier programa
• Contienen análisis por dominio y top dominios

🚨 PROBLEMAS COMUNES:
• "Error 403": El sitio bloquea bots
• "Error timeout": Sitio lento o no disponible
• "No se encontraron correos": Normal en muchos sitios
• "Error de conexión": Verifica tu internet

💡 CONSEJOS PRO:
• Ejecuta búsquedas en horarios de menor tráfico
• Si un sitio falla, inténtalo más tarde
• Combina con Google Dorks para encontrar más sitios
• Usa VPN para mayor privacidad
• Guarda los archivos generados como backup
""")

    def run(self):
        """Ejecuta el scrapper en modo consola"""
        print("🚀 Iniciando Scrapper Pro - Versión Consola...")
        
        while True:
            try:
                self.mostrar_menu()
                opcion = input("\n👆 Elige una opción: ").strip()
                
                if opcion == "1":
                    url = input("\n🌐 URL del sitio (ej: https://harvard.edu): ").strip()
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    max_pags = input("📄 Máximo páginas (default 30): ").strip()
                    max_pags = int(max_pags) if max_pags.isdigit() else 30
                    
                    self.scrapear_sitio(url, max_pags)
                    
                elif opcion == "2":
                    emails = self.buscar_en_lista_sitios(
                        self.universidades, 
                        "🎓 Búsqueda en Universidades Famosas",
                        "universidades"
                    )
                    
                elif opcion == "3":
                    emails = self.buscar_en_lista_sitios(
                        self.organizaciones,
                        "🏢 Búsqueda en Organizaciones",
                        "organizaciones"
                    )
                    
                elif opcion == "4":
                    print("\n🔍 BÚSQUEDA MASIVA - Todas las Fuentes")
                    print("⚠️ Esto puede tomar 15-20 minutos")
                    confirmar = input("¿Continuar? (s/n): ").lower()
                    
                    if confirmar.startswith('s'):
                        todas_fuentes = self.universidades + self.organizaciones
                        emails = self.buscar_en_lista_sitios(
                            todas_fuentes,
                            "🔍 Búsqueda Masiva (Universidades + Organizaciones)",
                            "busqueda_masiva"
                        )
                    else:
                        print("❌ Búsqueda masiva cancelada")
                        
                elif opcion == "5":
                    self.mostrar_google_dorks()
                    
                elif opcion == "6":
                    self.ver_archivos_generados()
                    
                elif opcion == "7":
                    self.mostrar_info_privacidad()
                    
                elif opcion == "8":
                    self.mostrar_ayuda()
                    
                elif opcion == "0":
                    print("\n👋 ¡Gracias por usar Scrapper Pro!")
                    print("📁 Tus archivos están guardados en:", os.path.abspath(self.results_dir))
                    print("⚖️ Recuerda usar los datos de forma ética y legal")
                    break
                    
                else:
                    print("\n❌ Opción no válida. Intenta de nuevo.")
                
                if opcion != "0":
                    input("\n⏸️ Presiona Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n\n⏹️ Programa interrumpido por el usuario")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {str(e)}")
                input("⏸️ Presiona Enter para continuar...")

if __name__ == "__main__":
    scrapper = ScrapperConsola()
    scrapper.run()
