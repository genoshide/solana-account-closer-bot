from colorlog import escape_codes

def print_banner(version="2.0.0-MultiThread"):
    """
    Prints the Genoshide ASCII banner and bot information.
    """
    banner = r"""
  ____                     _     _     _      
 / ___| ___ _ __   ___ ___| |__ (_) __| | ___ 
| |  _ / _ \ '_ \ / _ \ __| '_ \| |/ _` |/ _ \
| |_| |  __/ | | | (_) \__ \ | | | | (_| |  __/
 \____|\___|_| |_|\___/|___/_| |_|_|\__,_|\___|
                                              
    """
    
    # Adding colors using colorlog escape codes
    c_green = escape_codes['green']
    c_cyan = escape_codes['cyan']
    c_reset = escape_codes['reset']
    
    print(f"{c_green}{banner}{c_reset}")
    print(f"{c_cyan}[+] Genoshide Token Account Closer Bot{c_reset}")
    print(f"{c_cyan}[+] Version: {version}{c_reset}")
    print(f"{c_cyan}[+] Features: Multi-Account, Endless Loop, Async{c_reset}")
    print(f"{c_cyan}[+] Developer: Genoshide Team{c_reset}")
    print("=" * 60)
