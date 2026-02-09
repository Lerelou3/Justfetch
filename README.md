# JustFetch

**Ultra-fast, cross-platform system information tool with zero external dependencies.**

<p align="center">
  <img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python 3.6+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20BSD%20%7C%20Android-lightgrey.svg" alt="Platform support">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

## Features

-  **Blazing fast** – Executes in <0.2s on most systems
-  **Cross-platform** – Works on Windows, Linux, WSL2, macOS, BSD, Alpine, Termux/Android
-  **Beautiful ASCII art** – OS-specific logos (Windows, macOS, Linux, BSD)
-  **Zero dependencies** – Pure Python, no `pip install` required
-  **Comprehensive info** – CPU, RAM, disk, GPU, network, battery, temps, and more
-  **Highly modular** – Easy to customize and extend

## 📸 Screenshots

### Windows 11
```
                              .oodMMMM   user@hostname
                     .oodMMMMMMMMMMMMM   --------------
         ..oodMMM  MMMMMMMMMMMMMMMMMMM   OS       Windows 11 Éducation (26100)
   oodMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   Uptime   17h 42m
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   Shell    PowerShell
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   Screen   1920x1080
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   CPU      20-core i5-14500
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   GPU      RTX 3050 Ti [4.0GB]
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   RAM      12355/32454MB [###-------]
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   Disk     261.2/471.6GB (55%)
                                         IP       192.168.1.42 (WAN: 203.0.113.55)
   MMMMMMMMMMMMMM  MMMMMMMMMMMMMMMMMMM   Proc     280
   
   Fetch: 0.2541s
```

### Linux/WSL2
```
                                  user@hostname
            a8888b.               --------------
           d888888b.              OS       5.15.167.4 (WSL2)
           8P"YP"Y88              Uptime   2d 5h 23m
           8|o||o|88              Shell    zsh
           8'    .88              Pkgs     888 (dpkg)
           8`._.' Y8.             CPU      20-core Intel i7-12700H
          d/      `8b.            Temp     CPU: 55°C | GPU: 47°C
         dP   .    Y8b.           Use      CPU: 12% | GPU: 5%
        d8:'  "  `::88b           GPU      RTX 3050 Ti [0.5/4.0GB]
       d8"         'Y88b          RAM      2641/7796MB (SW: 0MB) [###-------]
      :8P    '      :888          Disk     48.0/1006.0GB (4%)
       8a.   :     _a88P          IP       172.29.111.184
     ._/"Yaa_:   .| 88P|          
     \    YP"    `| 8P  `.        
     /     \\.___.d|    .'         
     `--..__)8888P`._.'           
   
   Fetch: 0.1523s
```

## Quick Start

### Installation

**Option 1: Download directly**
```bash
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/justfetch/main/justfetch.py
python3 justfetch.py
```

**Option 2: Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/justfetch.git
cd justfetch
python3 justfetch.py
```

**Option 3: Make it globally available (Linux/macOS/WSL)**
```bash
sudo curl -o /usr/local/bin/justfetch https://raw.githubusercontent.com/YOUR_USERNAME/justfetch/main/justfetch.py
sudo chmod +x /usr/local/bin/justfetch
justfetch
```

### Requirements

- Python 3.6 or higher (standard library only)
- **Windows:** PowerShell (for some features)
- **Linux:** Standard `/proc` filesystem
- **Optional:** `nvidia-smi` for GPU temperature/usage

## Displayed Information

| Info | Description | Platforms |
|------|-------------|-----------|
| **OS** | Operating system version | All |
| **Uptime** | System uptime | All |
| **Shell** | Current shell | All |
| **Screen** | Display resolution | Windows, Linux (X11) |
| **Pkgs** | Installed packages | Linux (dpkg, pacman, apk), Termux |
| **CPU** | Processor model | All |
| **Temp** | CPU/GPU temperature | Linux (native), Windows (limited) |
| **Use** | CPU/GPU usage % | All |
| **GPU** | Graphics card info | NVIDIA (via nvidia-smi) |
| **RAM** | Memory usage with bar | All |
| **Disk** | Storage usage | All |
| **IP** | LAN + WAN IP address | All (WAN requires internet) |
| **Proc** | Running processes count | Windows, Linux |
| **Batt** | Battery status | Laptops only |

## Configuration

Edit the `CONFIG` dictionary at the top of the script:

```python
CONFIG = {
    "SHOW_VRAM_ON_WSL": True,        # Show GPU VRAM on WSL2
    "SHOW_PUBLIC_IP": True,          # Fetch public IP (requires internet)
    "PUBLIC_IP_TIMEOUT": 2.0,        # Timeout for public IP fetch
    "CPU_USAGE_SAMPLE_TIME": 0.03,   # CPU usage sample delay
}
```

## Customization

### Add a new info line

1. Create a collector function:
```python
@safe
def get_my_info():
    return "My custom value"
```

2. Add it to `build_info()`:
```python
data.append(("Label", get_my_info()))
```

### Change colors

Modify the `C` dictionary:
```python
C = {
    "c": "\033[96m",  # Cyan → change to your color
    "g": "\033[92m",  # Green
    # ...
}
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **Windows 10/11** | ✅ Full | All features supported |
| **Linux** | ✅ Full | Native hardware access |
| **WSL2** | ✅ Partial | No CPU temp (VM limitation) |
| **macOS** | ✅ Basic | Limited sensor access |
| **BSD** | ✅ Basic | FreeBSD, OpenBSD, NetBSD |
| **Alpine Linux** | ✅ Full | apk package manager support |
| **Termux (Android)** | ✅ Full | Optimized for mobile |

## Troubleshooting

**Q: CPU temperature shows nothing**  
A: On Windows/WSL2, CPU temp is not accessible without third-party tools. On Linux, ensure `/sys/class/hwmon/` exists.

**Q: Public IP not showing**  
A: Check firewall settings or increase `PUBLIC_IP_TIMEOUT` in config.

**Q: GPU not detected**  
A: Install `nvidia-smi` (NVIDIA drivers) or check that your GPU is NVIDIA.

**Q: Battery shows "-1%" on desktop**  
A: This is a Windows bug with some motherboards. The script should hide this line automatically.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Inspired by [neofetch](https://github.com/dylanaraps/neofetch) and [fastfetch](https://github.com/fastfetch-cli/fastfetch)
- ASCII art adapted from various sources

---

**⭐ If you find this useful, please star the repo!**
