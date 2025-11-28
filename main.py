import time
import json
import click
import os
import hashlib  # Dùng để băm dữ liệu cho Schnorr
from abc import ABC, abstractmethod
from tabulate import tabulate

# Thư viện BIP39 Mnemonic
from mnemonic import Mnemonic

# Thư viện cho ECDSA (Ethereum)
from eth_keys import keys
from eth_utils import decode_hex, to_checksum_address

# Thư viện cho Ed25519 (Solana/Modern)
import nacl.signing
import nacl.encoding

# Thư viện cho Schnorr (Bitcoin Taproot)
import coincurve

# --- CẤU HÌNH ---
KEYSTORE_FILE = "keystore.json"

# --- PHẦN 1: CORE ARCHITECTURE (STRATEGY PATTERN) ---

class CryptoStrategy(ABC):
    """Lớp trừu tượng định nghĩa chuẩn cho mọi thuật toán ký"""
    
    @abstractmethod
    def generate_keypair_from_seed(self, seed_bytes):
        pass
    
    @abstractmethod
    def get_address(self, public_key):
        pass
    
    @abstractmethod
    def sign_message(self, private_key, message):
        pass

# --- PHẦN 2: TRIỂN KHAI CÁC THUẬT TOÁN ---

class ECDSA_Ethereum(CryptoStrategy):
    def generate_keypair_from_seed(self, seed_bytes):
        private_key_bytes = seed_bytes[:32] 
        pk = keys.PrivateKey(private_key_bytes)
        return pk, pk.public_key

    def get_address(self, public_key):
        return public_key.to_checksum_address()

    def sign_message(self, private_key, message):
        try:
            # eth_keys tự động hash bằng Keccak bên trong sign_msg
            message_bytes = message.encode('utf-8')
            signature = private_key.sign_msg(message_bytes)
            return signature.to_hex()
        except Exception as e:
            return f"Error: {str(e)}"

class Ed25519_Solana(CryptoStrategy):
    def generate_keypair_from_seed(self, seed_bytes):
        private_key_bytes = seed_bytes[:32]
        pk = nacl.signing.SigningKey(private_key_bytes)
        return pk, pk.verify_key

    def get_address(self, public_key):
        return public_key.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')

    def sign_message(self, private_key, message):
        message_bytes = message.encode('utf-8')
        signed = private_key.sign(message_bytes)
        return signed.signature.hex()

class Schnorr_Bitcoin(CryptoStrategy):
    def generate_keypair_from_seed(self, seed_bytes):
        private_key_bytes = seed_bytes[:32]
        pk = coincurve.PrivateKey(private_key_bytes)
        return pk, pk.public_key

    def get_address(self, public_key):
        return public_key.format(compressed=True)[1:].hex()

    def sign_message(self, private_key, message):
        message_bytes = message.encode('utf-8')
        # FIX: Hash message thành 32 bytes (SHA256) trước khi đưa vào coincurve
        message_hash = hashlib.sha256(message_bytes).digest()
        return private_key.sign(message_hash, hasher=None).hex()

# --- PHẦN 3: WALLET MANAGER & PERSISTENCE ---

class WalletManager:
    def __init__(self):
        self.strategies = {
            "ecdsa": ECDSA_Ethereum(),
            "ed25519": Ed25519_Solana(),
            "schnorr": Schnorr_Bitcoin()
        }
        self.current_wallet = None
        self.mnemo = Mnemonic("english")
        
        # Tự động tải ví cũ nếu có
        self.load_from_disk()

    def create_mnemonic(self):
        return self.mnemo.generate(strength=128)

    def load_wallet_from_mnemonic(self, mnemonic_phrase, algo, save=False):
        """Khôi phục ví từ Mnemonic và tùy chọn lưu xuống đĩa"""
        if not self.mnemo.check(mnemonic_phrase):
            return None, "Invalid Mnemonic Phrase!"

        strategy = self.strategies.get(algo)
        if not strategy:
            return None, "Algorithm not supported"

        seed = self.mnemo.to_seed(mnemonic_phrase)
        priv, pub = strategy.generate_keypair_from_seed(seed)
        addr = strategy.get_address(pub)

        self.current_wallet = {
            "algo": algo,
            "priv": priv,
            "pub": pub,
            "address": addr,
            "mnemonic": mnemonic_phrase
        }
        
        if save:
            self.save_to_disk()
        
        # Format key để hiển thị
        if algo == "ecdsa" or algo == "schnorr":
            priv_hex = priv.to_hex()
        else:
            priv_hex = priv.encode(encoder=nacl.encoding.HexEncoder).decode('utf-8')
            
        return {
            "Algorithm": algo.upper(),
            "Address": addr,
            "Private Key": priv_hex[:6] + "..." + priv_hex[-4:],
            "Status": "Active"
        }, None

    def sign_transaction(self, message):
        if not self.current_wallet:
            return None, "No wallet loaded. Use 'create' or 'recover' first."
        
        algo = self.current_wallet["algo"]
        priv = self.current_wallet["priv"]
        strategy = self.strategies[algo]
        
        start_time = time.perf_counter_ns()
        signature = strategy.sign_message(priv, message)
        end_time = time.perf_counter_ns()
        
        return {
            "Message": message,
            "Signature": signature[:32] + "..." + signature[-32:], 
            "Algorithm": algo.upper()
        }, (end_time - start_time) / 1000

    # --- TÍNH NĂNG LƯU TRỮ (PERSISTENCE) ---
    def save_to_disk(self):
        """Lưu mnemonic và thuật toán vào file JSON"""
        if not self.current_wallet:
            return
        data = {
            "mnemonic": self.current_wallet["mnemonic"],
            "algo": self.current_wallet["algo"]
        }
        with open(KEYSTORE_FILE, "w") as f:
            json.dump(data, f)

    def load_from_disk(self):
        """Đọc file JSON và khôi phục ví"""
        if not os.path.exists(KEYSTORE_FILE):
            return
        try:
            with open(KEYSTORE_FILE, "r") as f:
                data = json.load(f)
            # Tải lại ví nhưng không cần save lần nữa
            self.load_wallet_from_mnemonic(data["mnemonic"], data["algo"], save=False)
        except Exception:
            pass # Bỏ qua nếu file lỗi

# Khởi tạo Manager (Sẽ tự động load file keystore.json nếu có)
wm = WalletManager()

# --- PHẦN 4: CLI COMMANDS ---

@click.group()
def cli():
    """Ứng dụng quản lý Ví Blockchain (Có tính năng Auto-Save)"""
    pass

@cli.command()
@click.option('--algo', default='ecdsa', type=click.Choice(['ecdsa', 'ed25519', 'schnorr']), help='Chọn thuật toán.')
def create(algo):
    """Tạo ví mới và tự động lưu."""
    mnemonic = wm.create_mnemonic()
    click.echo("\n[!] ĐANG TẠO VÍ MỚI...")
    click.echo("-" * 50)
    click.echo(f"SECRET PHRASE: {mnemonic}")
    click.echo("-" * 50)
    
    # Load và Save xuống đĩa
    res, err = wm.load_wallet_from_mnemonic(mnemonic, algo, save=True)
    if err:
        click.echo(f"Error: {err}")
    else:
        click.echo("✔ Đã lưu ví vào 'keystore.json'")
        click.echo(tabulate([res.values()], headers=res.keys(), tablefmt="fancy_grid"))

@cli.command()
@click.option('--words', prompt='Nhập 12 từ khóa', help='Chuỗi 12 từ mnemonic.')
@click.option('--algo', default='ecdsa', type=click.Choice(['ecdsa', 'ed25519', 'schnorr']))
def recover(words, algo):
    """Khôi phục ví và lưu lại."""
    click.echo(f"\n[!] ĐANG KHÔI PHỤC VÍ ({algo.upper()})...")
    res, err = wm.load_wallet_from_mnemonic(words, algo, save=True)
    
    if err:
        click.echo(f"LỖI: {err}")
    else:
        click.echo("✔ Đã lưu ví vào 'keystore.json'")
        click.echo(tabulate([res.values()], headers=res.keys(), tablefmt="fancy_grid"))

@cli.command()
@click.argument('message')
def sign(message):
    """Ký thông điệp (Sử dụng ví đã lưu)."""
    res, duration = wm.sign_transaction(message)
    if not res:
        click.echo(f"Lỗi: {duration}")
        return

    click.echo(f"\n--- KÝ THÀNH CÔNG ---")
    click.echo(json.dumps(res, indent=2))
    click.echo(f"Thời gian: {duration:.2f} microseconds\n")

@cli.command()
def info():
    """Xem thông tin ví đang lưu."""
    if wm.current_wallet:
        click.echo(f"\nVí đang sử dụng: {wm.current_wallet['algo'].upper()}")
        click.echo(f"Địa chỉ: {wm.current_wallet['address']}")
    else:
        click.echo("\nChưa có ví nào được lưu. Hãy dùng lệnh 'create' hoặc 'recover'.")

@cli.command()
def benchmark():
    """So sánh tốc độ."""
    click.echo("\n--- BENCHMARK ---")
    results = []
    # Sử dụng mnemonic ngẫu nhiên để test
    temp_mnemo = wm.create_mnemonic()
    
    for algo in ['ecdsa', 'ed25519', 'schnorr']:
        start = time.time()
        for _ in range(50):
            wm.load_wallet_from_mnemonic(temp_mnemo, algo, save=False)
        load_t = (time.time() - start) * 20
        
        # Load ví vào RAM trước khi test sign
        wm.load_wallet_from_mnemonic(temp_mnemo, algo, save=False)
        start = time.time()
        for _ in range(50):
            wm.sign_transaction("Benchmark Payload Test 12345")
        sign_t = (time.time() - start) * 20
        results.append([algo, f"{load_t:.2f}ms", f"{sign_t:.2f}ms"])
    
    print(tabulate(results, headers=["Algo", "Derivation (1000x)", "Signing (1000x)"], tablefmt="grid"))

if __name__ == '__main__':
    cli()