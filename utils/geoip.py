import requests
import re

def get_geo_info(ip_address):
    url = f"http://ipinfo.io/{ip_address}/json"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def extract_ip_addresses(text):
    # Регулярное выражение для поиска IPv4 адресов
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # Найти все совпадения в тексте
    ip_addresses = re.findall(ip_pattern, text)
    return ip_addresses