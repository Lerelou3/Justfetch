#!/usr/bin/env python3
"""
JustFetch (v2026) - Ultimate Cross-Platform Edition
Supports: Windows, Linux, WSL2, macOS, BSD, Alpine, Termux/Android
Features: Smart detection, modular architecture, <0.2s execution
"""

import os, platform, time, socket, sys, shutil, ctypes, mmap

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION - Customize behavior here
# ═══════════════════════════════════════════════════════════════════════════

CONFIG = {
    "SHOW_VRAM_ON_WSL": True,      # Show GPU VRAM even on WSL2
    "SHOW_PUBLIC_IP": True,        # Fetch public IP (requires internet)
    "PUBLIC_IP_TIMEOUT": 2.0,      # Timeout for public IP fetch (seconds)
    "CPU_USAGE_SAMPLE_TIME": 0.03, # CPU usage sampling delay (seconds)
}

# ═══════════════════════════════════════════════════════════════════════════
# PLATFORM DETECTION
# ═══════════════════════════════════════════════════════════════════════════

IS_WINDOWS = os.name == 'nt'
IS_BSD = sys.platform.startswith(('freebsd', 'openbsd', 'netbsd'))
IS_MACOS = sys.platform == 'darwin'

def is_wsl():
    """Check if running under WSL/WSL2."""
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    return False

def is_alpine():
    """Check if running on Alpine Linux."""
    return os.path.exists("/etc/alpine-release")

def is_termux():
    """Check if running in Termux on Android."""
    home = os.environ.get("HOME", "")
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in home or "/data/data/com.termux" in prefix

if IS_WINDOWS:
    import winreg

# ═══════════════════════════════════════════════════════════════════════════
# COLOR SCHEMES
# ═══════════════════════════════════════════════════════════════════════════

C = {
    "c": "\033[96m", "g": "\033[92m", "y": "\033[93m", "b": "\033[94m",
    "r": "\033[91m", "bold": "\033[1m", "d": "\033[2m", "res": "\033[0m",
    "white": "\033[97m", "gray": "\033[90m", "dblue": "\033[34m",
    "orange": "\033[38;5;208m",
}

def temp_color(temp):
    """Return color based on temperature."""
    if temp is None: return C['d']
    if temp < 50: return C['g']
    if temp < 70: return C['y']
    if temp < 85: return C['orange']
    return C['r']

# ═══════════════════════════════════════════════════════════════════════════
# ASCII ART - Add new logos here
# ═══════════════════════════════════════════════════════════════════════════

LOGOS = {
    "apple": ([
        "                    ", "        .:'         ", "     __ :'__        ",
        "   .'`  `-'  ``.    ", "  :          .-'    ", "  :         :       ",
        "   :         `-;    ", "    `.__.-.__.'     "
    ], C['white']),
    
    "bsd": ([
        "               ,        ,          ", "              /(        )`         ",
        "             \\ \\___   / |         ", "             /- _  `-/  '          ",
        "            (/\\/ \\ \\   /\\         ", "            / /   | `    \\         ",
        "            O O   ) /    |         ", "            `-^--'`<     '         ",
        "           (_.)  _  )   /          ", "            `.___/`    /           ",
        "              `-----' /            ", "     <----.     __ / __   \\       ",
        "     <----|====O)))==) \\) /====|  ", "     <----'    `--' `.__,' \\      ",
        "                  |        |       ", "                   \\       /       ",
        "              ______( (_  / \\_____ ", "            ,'  ,-----'   |        ",
        "            `--{________})        "
    ], C['r']),
    
    "windows": ([
        "                            .oodMMMM", "                   .oodMMMMMMMMMMMMM",
        "       ..oodMMM  MMMMMMMMMMMMMMMMMMM", " oodMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", "                                    ",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM",
        " MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM", " `^^^^^^MMMMMMM  MMMMMMMMMMMMMMMMMMM",
        "       ````^^^^  ^^MMMMMMMMMMMMMMMMM", "                      ````^^^^^^MMMM"
    ], C['dblue']),
    
    "linux": ([
        "                            ", "          a8888b.            ",
        "         d888888b.           ", "         8P\"YP\"Y88           ",
        "         8|o||o|88           ", "         8'    .88           ",
        "         8`._.' Y8.          ", "        d/      `8b.         ",
        "       dP   .    Y8b.        ", "      d8:'  \"  `::88b        ",
        "     d8\"         'Y88b       ", "    :8P    '      :888       ",
        "     8a.   :     _a88P       ", "   ._/\"Yaa_:   .| 88P|       ",
        "   \\    YP\"    `| 8P  `.     ", "   /     \\.___.d|    .'      ",
        "   `--..__)8888P`._.'        "
    ], C['gray']),
}

def detect_logo():
    """Select appropriate logo based on OS."""
    if IS_MACOS: return LOGOS["apple"]
    if IS_WINDOWS: return LOGOS["windows"]
    if IS_BSD: return LOGOS["bsd"]
    return LOGOS["linux"]

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY DECORATORS
# ═══════════════════════════════════════════════════════════════════════════

def safe(func):
    """Wrapper to catch all exceptions and return None."""
    def wrapper(*args, **kwargs):
        try: return func(*args, **kwargs)
        except: return None
    return wrapper

# ═══════════════════════════════════════════════════════════════════════════
# DATA COLLECTORS - Add new info functions here
# ═══════════════════════════════════════════════════════════════════════════

@safe
def get_os():
    """OS name and version."""
    rel = platform.release()
    
    if IS_WINDOWS:
        # Détection Windows 11 vs 10
        build = int(platform.version().split('.')[2]) if '.' in platform.version() else 0
        
        # Windows 11 commence au build 22000
        if build >= 22000:
            win_name = "Windows 11"
        else:
            win_name = "Windows 10"
        
        # Essayer de récupérer l'édition (Pro, Home, Education, etc.)
        edition = None
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-Command', '(Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion").EditionID'],
                capture_output=True,
                text=True,
                timeout=0.5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            edition_raw = result.stdout.strip()
            # Traduction des éditions communes
            edition_map = {
                "Education": "Éducation",
                "Professional": "Pro",
                "Core": "Famille",
                "Enterprise": "Entreprise"
            }
            edition = edition_map.get(edition_raw, edition_raw)
        except:
            pass
        
        # Format final : "Windows 11 Éducation (26100)"
        version_str = f"{win_name}"
        if edition:
            version_str += f" {edition}"
        version_str += f" ({build})"
        
        return version_str
    
    if is_termux(): 
        return f"Android/Termux {rel}"
    
    if is_alpine(): 
        return f"Alpine {rel}"
    
    if IS_MACOS: 
        return f"macOS {platform.mac_ver()[0]}"
    
    if IS_BSD: 
        return f"{platform.system()} {rel.split('-')[0]}"
    
    # Linux - Lire /etc/os-release pour avoir le vrai nom (pas juste le kernel)
    if os.path.exists("/etc/os-release"):
        try:
            os_info = {}
            with open("/etc/os-release") as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_info[key] = value.strip('"')
            
            # Utiliser PRETTY_NAME si disponible (ex: "Debian GNU/Linux 13 (trixie)")
            # Sinon fallback sur NAME + VERSION
            name = os_info.get("PRETTY_NAME")
            if not name:
                name = os_info.get("NAME", "Linux")
                version = os_info.get("VERSION", "")
                if version:
                    name += f" {version}"
            
            # Ajouter (WSL2) si détecté
            if is_wsl():
                name += " (WSL2)"
            
            return name
        except: 
            pass
    
    # Fallback si /etc/os-release n'existe pas
    if is_wsl(): 
        return f"{rel.split('-')[0]} (WSL2)"
    
    return rel.split("-")[0]

@safe
def get_packages():
    """Installed package count."""
    if IS_WINDOWS or IS_MACOS: return None
    
    # Termux dpkg
    prefix = os.environ.get("PREFIX")
    if prefix:
        termux_status = os.path.join(prefix, "var/lib/dpkg/status")
        if os.path.exists(termux_status):
            try:
                count = 0
                with open(termux_status, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("Package: "):
                            count += 1
                return f"{count} (dpkg)"
            except: pass
    
    # Standard dpkg - FIX: Lire ligne par ligne
    if os.path.exists("/var/lib/dpkg/status"):
        try:
            count = 0
            with open("/var/lib/dpkg/status", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.startswith("Package: "):
                        count += 1
            return f"{count} (dpkg)"
        except: pass
    
    # Pacman
    if os.path.exists("/var/lib/pacman/local"):
        try:
            # Exclure le fichier ALPM_DB_VERSION qui n'est pas un paquet
            count = len([d for d in os.listdir('/var/lib/pacman/local') if not d.startswith('ALPM')])
            return f"{count} (pacman)"
        except: pass
    
    # Alpine apk
    if is_alpine():
        for p in ("/lib/apk/db/installed", "/var/lib/apk/db/installed"):
            if os.path.exists(p):
                try:
                    count = 0
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.startswith("P:"):
                                count += 1
                    return f"{count} (apk)"
                except: break
    
    return None


@safe
def get_uptime():
    """System uptime."""
    sec = None
    if IS_WINDOWS:
        sec = ctypes.windll.kernel32.GetTickCount64() / 1000
    elif os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r") as f:
                sec = float(f.read().split()[0])
        except: pass
    
    if sec is None and not IS_WINDOWS:
        import subprocess
        try:
            out = subprocess.check_output(["uptime", "-p"], text=True, timeout=0.3).strip()
            return out.replace("up ", "")
        except: return "N/A"
    
    if sec is None: return "N/A"
    m, _ = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    parts.append(f"{m}m")
    return " ".join(parts)

@safe
def get_shell():
    """Current shell."""
    shell = os.path.basename(os.environ.get("SHELL") or os.environ.get("COMSPEC") or "sh")
    if IS_WINDOWS and "powershell" in os.environ.get("PSModulePath", "").lower():
        shell = "PowerShell"
    return shell

@safe
def get_cpu():
    """CPU model."""
    cores = os.cpu_count()
    
    if IS_WINDOWS:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            model, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            model = model.replace("Intel(R)", "").replace("Core(TM)", "").replace("AMD", "").strip()
            return f"{cores}-core {model}"
        except: pass
    
    if is_termux() or "android" in platform.platform().lower():
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if any(k in line for k in ["Hardware", "model name", "Processor"]):
                        model = line.split(":", 1)[1].strip()
                        return f"{cores}-core {model}"
    
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    model = line.split(":", 1)[1].strip().replace("(R)", "").replace("(TM)", "").replace("CPU", "").strip()
                    return f"{cores}-core {model}"
    
    return f"{cores}-core {platform.machine()}"

@safe
def get_cpu_temp():
    """CPU temperature (native Linux only)."""
    if IS_WINDOWS or is_wsl(): return None
    
    if os.path.exists("/sys/class/hwmon/"):
        try:
            import glob
            for hwmon in glob.glob('/sys/class/hwmon/hwmon*'):
                name_file = f"{hwmon}/name"
                if os.path.exists(name_file):
                    with open(name_file) as f:
                        if f.read().strip() in ["coretemp", "k10temp", "zenpower"]:
                            temp_file = f"{hwmon}/temp1_input"
                            if os.path.exists(temp_file):
                                with open(temp_file) as f:
                                    temp = int(f.read().strip()) / 1000.0
                                    if 10 < temp < 120: return int(temp)
        except: pass
    return None

@safe
def get_cpu_usage():
    """CPU usage percentage."""
    if IS_WINDOWS:
        try:
            import subprocess
            result = subprocess.run(['typeperf', r'\Processor(_Total)\% Processor Time', '-sc', '1'],
                capture_output=True, text=True, timeout=0.5, creationflags=subprocess.CREATE_NO_WINDOW)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                return int(float(lines[-1].split(',')[-1].strip('"')))
        except: pass
    
    elif os.path.exists("/proc/stat"):
        try:
            def read(): 
                with open("/proc/stat") as f:
                    vals = [int(x) for x in f.readline().split()[1:]]
                    return sum(vals), vals[3]
            total1, idle1 = read()
            time.sleep(CONFIG["CPU_USAGE_SAMPLE_TIME"])
            total2, idle2 = read()
            diff_total = total2 - total1
            if diff_total > 0:
                return int(100 * (1 - (idle2 - idle1) / diff_total))
        except: pass
    return None

@safe
def get_gpus():
    """GPU info with temp/usage."""
    gpus = []
    should_use_smi = IS_WINDOWS or (CONFIG["SHOW_VRAM_ON_WSL"] and shutil.which("nvidia-smi"))
    
    if should_use_smi and shutil.which("nvidia-smi"):
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1.0)
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    p = line.strip().split(', ')
                    if len(p) >= 3:
                        name = p[0].replace("NVIDIA ", "").replace("GeForce ", "")
                        vram = f"[{int(p[1])/1024:.1f}/{int(p[2])/1024:.1f}GB]"
                        temp = int(p[3]) if len(p) >= 4 and p[3].isdigit() else None
                        usage = int(p[4]) if len(p) >= 5 and p[4].isdigit() else None
                        gpus.append((name, vram, temp, usage))
            if gpus: return gpus
        except: pass
    
    if not IS_WINDOWS and not IS_MACOS:
        path = "/proc/driver/nvidia/gpus/"
        if os.path.exists(path):
            try:
                for d in os.listdir(path):
                    if d != ".":
                        with open(f"{path}/{d}/information") as f:
                            for line in f:
                                if "Model:" in line:
                                    gpus.append((line.split(":", 1)[1].strip().replace("NVIDIA ", ""), "", None, None))
                                    break
            except: pass
        if not gpus and os.path.exists("/dev/dxg"):
            return [("WSL2 Virtual GPU", "", None, None)]
    return gpus

@safe
def get_ram():
    """RAM usage."""
    if IS_WINDOWS:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total = stat.ullTotalPhys // 1048576
        used = total - (stat.ullAvailPhys // 1048576)
        pct = used / total
        bar = f"{C['g']}{'#'*int(pct*10)}{C['d']}{'-'*int((1-pct)*10)}"
        return f"{used}/{total}MB [{bar}{C['res']}]"
    
    elif os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            m = {}
            for line in f:
                p = line.split()
                if len(p) >= 2: m[p[0].rstrip(':')] = int(p[1])
        total = m.get("MemTotal", 0) // 1024
        if total == 0: return "N/A"
        avail = m.get("MemAvailable", m.get("MemFree", 0) + m.get("Buffers", 0) + m.get("Cached", 0)) // 1024
        used = total - avail
        sw = (m.get("SwapTotal", 0) - m.get("SwapFree", 0)) // 1024
        pct = used / total
        bar = f"{C['g']}{'#'*int(pct*10)}{C['d']}{'-'*int((1-pct)*10)}"
        return f"{used}/{total}MB (SW: {sw}MB) [{bar}{C['res']}]"
    return "N/A"

@safe
def get_disk():
    """Disk usage."""
    if IS_WINDOWS:
        path = "C:\\"
    elif is_termux():
        path = os.environ.get("HOME", "/")
    else:
        path = "/"
    
    total, used, _ = shutil.disk_usage(path)
    total_gb, used_gb = total / (1024**3), used / (1024**3)
    pct = int((used / total) * 100) if total_gb > 0 else 0
    return f"{used_gb:.1f}/{total_gb:.1f}GB ({pct}%)"

@safe
def get_ip_lan():
    """LAN IP for SSH on local network."""
    ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except: pass
    
    if not ip or ip.startswith("127."):
        try:
            ip2 = socket.gethostbyname(socket.gethostname())
            if ip2 and not ip2.startswith("127."): ip = ip2
        except: pass
    
    return ip if ip and not ip.startswith("127.") else "127.0.0.1"

@safe
def get_ip_wan():
    """Public IP for SSH from internet."""
    if not CONFIG["SHOW_PUBLIC_IP"]: return None
    
    # Liste de services (fallback si ifconfig.me est bloqué)
    services = [
        "https://ifconfig.me/ip",
        "https://api.ipify.org",
        "https://icanhazip.com"
    ]
    
    for service in services:
        try:
            import urllib.request
            with urllib.request.urlopen(service, timeout=CONFIG["PUBLIC_IP_TIMEOUT"]) as r:
                ip = r.read().decode().strip()
                # Validation simple d'IP
                if ip and ip.count('.') == 3:
                    return ip
        except:
            continue
    return None

@safe
def get_battery():
    """Battery status."""
    if IS_WINDOWS:
        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
        s = SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
            # Convertir c_byte signé en non-signé (0-255)
            battery_flag = s.BatteryFlag & 0xFF
            battery_percent = s.BatteryLifePercent & 0xFF
            
            # PC fixe sans batterie : BatteryFlag = 128 ou BatteryPercent = 255
            if battery_flag == 128 or battery_percent == 255:
                return None
            
            # Batterie valide (0-100%)
            if 0 <= battery_percent <= 100:
                return f"{'AC' if s.ACLineStatus == 1 else 'Bat'} {battery_percent}%"
        return None
    
    base = "/sys/class/power_supply/"
    if os.path.exists(base):
        for bat in [b for b in os.listdir(base) if b.startswith("BAT")]:
            try:
                p = f"{base}/{bat}"
                with open(f"{p}/capacity") as f: cap = f.read().strip()
                with open(f"{p}/status") as f: stat = f.read().strip()
                return f"{'AC' if stat == 'Charging' else 'OK'} {cap}%"
            except: continue
    return None

@safe
def get_resolution():
    """Screen resolution."""
    if IS_WINDOWS:
        try:
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            return f"{width}x{height}"
        except: pass
    elif not IS_MACOS:  # Linux/BSD
        try:
            import subprocess
            result = subprocess.run(['xrandr'], capture_output=True, text=True, timeout=0.3)
            for line in result.stdout.split('\n'):
                if '*' in line:  # Current resolution
                    res = line.split()[0]
                    return res
        except: pass
    return None

@safe
def get_processes():
    """Number of running processes."""
    if IS_WINDOWS:
        try:
            import subprocess
            result = subprocess.run(
                ['tasklist'], 
                capture_output=True, 
                text=True, 
                timeout=0.5, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Chaque ligne = un processus (sauf les 3 premières lignes d'en-tête)
            count = len(result.stdout.strip().split('\n')) - 3
            return str(count) if count > 0 else None
        except: 
            pass
    elif os.path.exists("/proc"):
        try:
            # Compter les dossiers numériques dans /proc (chaque PID = 1 processus)
            count = sum(1 for d in os.listdir("/proc") if d.isdigit())
            return str(count) if count > 0 else None
        except: 
            pass
    return None

# ═══════════════════════════════════════════════════════════════════════════
# MAIN RENDERING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def build_info():
    """Build info list - ADD NEW FEATURES HERE."""
    data = []
    
    # Basic info
    data.append(("OS", get_os()))
    data.append(("Uptime", get_uptime()))
    data.append(("Shell", get_shell()))
    data.append(("Screen", get_resolution()))
    data.append(("Pkgs", get_packages()))
    data.append(("CPU", get_cpu()))
    
    # Temperature line
    temp_parts = []
    cpu_temp = get_cpu_temp()
    if cpu_temp:
        temp_parts.append(f"CPU: {temp_color(cpu_temp)}{cpu_temp}°C{C['res']}")
    
    gpu_list = get_gpus()
    if gpu_list:
        for i, (name, vram, temp, usage) in enumerate(gpu_list):
            if temp:
                label = "GPU" if len(gpu_list) == 1 else f"GPU{i}"
                temp_parts.append(f"{label}: {temp_color(temp)}{temp}°C{C['res']}")
    
    if temp_parts:
        data.append(("Temp", " | ".join(temp_parts)))
    
    # Usage line
    use_parts = []
    cpu_usage = get_cpu_usage()
    if cpu_usage is not None:
        use_parts.append(f"CPU: {C['c']}{cpu_usage}%{C['res']}")
    
    if gpu_list:
        for i, (name, vram, temp, usage) in enumerate(gpu_list):
            if usage is not None:
                label = "GPU" if len(gpu_list) == 1 else f"GPU{i}"
                use_parts.append(f"{label}: {C['c']}{usage}%{C['res']}")
    
    if use_parts:
        data.append(("Use", " | ".join(use_parts)))
    
    # GPU names
    if gpu_list:
        for i, (name, vram, temp, usage) in enumerate(gpu_list):
            label = "GPU" if len(gpu_list) == 1 else f"GPU {i}"
            data.append((label, f"{name} {C['d']}{vram}{C['res']}" if vram else name))
    
    # System resources
    data.append(("RAM", get_ram()))
    data.append(("Disk", get_disk()))
    
    # Network
    lan_ip = get_ip_lan()
    wan_ip = get_ip_wan()
    ip_value = lan_ip
    if wan_ip and wan_ip != lan_ip:
        ip_value = f"{lan_ip} {C['d']}(WAN: {wan_ip}){C['res']}"
    data.append(("IP", ip_value))
    
    data.append(("Batt", get_battery()))

    data.append(("Proc", get_processes()))
    
    return data

def render():
    """Main rendering function."""
    start = time.monotonic()
    
    # Header
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
    host = socket.gethostname() if socket.gethostname() else "localhost"
    
    lines = [
        f"{C['c']}{C['bold']}{user}{C['res']}@{C['c']}{host}{C['res']}",
        f"{C['g']}{'-' * (len(user) + len(host) + 1)}{C['res']}"
    ]
    
    # Info
    for k, v in build_info():
        if v: lines.append(f"{C['y']}{k.ljust(8)}{C['res']} {v}")
    
    # Color palette
    lines.append("")
    lines.append(''.join([f'\033[4{i}m  ' for i in range(1, 7)]) + C['res'])
    
    # Logo
    logo, color = detect_logo()
    logo_width = max(len(x) for x in logo)
    
    # Render side-by-side
    print()
    for i in range(max(len(logo), len(lines))):
        logo_seg = (logo[i] if i < len(logo) else " " * logo_width).ljust(logo_width)
        info_seg = lines[i] if i < len(lines) else ""
        print(f"  {color}{logo_seg}{C['res']}   {info_seg}")
    
    # Footer
    elapsed = time.monotonic() - start
    print(f"\n   {C['d']}Fetch: {elapsed:.4f}s{C['res']}\n")

if __name__ == "__main__":
    render()
