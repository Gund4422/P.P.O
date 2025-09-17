# ------------------------------
# Docksterling 3.0 – Luraph Mode
# ------------------------------
import random, re, argparse, sys
from pathlib import Path

# ---------------------
# Helper functions
# ---------------------
def random_name(length=None):
    if not length:
        length = random.randint(6, 12)
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ''.join(random.choice(chars) for _ in range(length))

def random_math_expr(n, depth=0):
    """Recursive nested math obfuscation"""
    if depth > 2 or n < 2:  # avoid infinite recursion
        return str(n)
    ops = ['+', '-', '*', '^', '|', '&', '<<', '>>']
    op = random.choice(ops)
    if op == '+':
        a = random.randint(0, n)
        b = n - a
        return f"({random_math_expr(a, depth+1)}+{random_math_expr(b, depth+1)})"
    elif op == '-':
        a = n + random.randint(1, 20)
        b = a - n
        return f"({random_math_expr(a, depth+1)}-{random_math_expr(b, depth+1)})"
    elif op == '*':
        factors = [(i, n//i) for i in range(1, n+1) if n % i == 0]
        if factors:
            a, b = random.choice(factors)
            return f"({random_math_expr(a, depth+1)}*{random_math_expr(b, depth+1)})"
        return str(n)
    elif op == '^':
        return f"({n}^0)"
    elif op == '|':
        return f"({n}|0)"
    elif op == '&':
        return f"({n}&{n})"
    elif op == '<<':
        return f"({n}<<0)"
    elif op == '>>':
        return f"({n}>>0)"
    return str(n)

def xor_encrypt(data_bytes, key):
    return bytes(b ^ key for b in data_bytes)

def encode_string_math(s):
    return ','.join(random_math_expr(b) for b in s)

# ---------------------
# Renaming identifiers
# ---------------------
def rename_identifiers(lua_code):
    funcs = list(set(re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', lua_code)))
    locals_found = list(set(re.findall(r'\blocal\s+([a-zA-Z_][a-zA-Z0-9_]*)', lua_code)))
    globals_found = list(set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=', lua_code)))
    
    rename_map = {f: random_name() for f in funcs + locals_found + globals_found}
    if rename_map:
        pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in rename_map.keys()) + r')\b')
        lua_code = pattern.sub(lambda m: rename_map[m.group(0)], lua_code)
    return lua_code

# ---------------------
# Literal encryption
# ---------------------
def encrypt_literals(lua_code, xor_key=0x55):
    string_pattern = re.compile(r'"(.*?)"')
    lua_code = string_pattern.sub(lambda m: f'string.char({encode_string_math(xor_encrypt(m.group(1).encode(), xor_key))})', lua_code)
    
    number_pattern = re.compile(r'\b\d+\b')
    lua_code = number_pattern.sub(lambda m: random_math_expr(int(m.group(0))), lua_code)
    return lua_code

# ---------------------
# Junk and control flow
# ---------------------
JUNK_TEMPLATES = [
    "if false then local {}={} end",
    "repeat until true",
    "for i=1,0 do end",
    "::{}::",
    "local {}={}; {}={} or {}",
    "function {}() return {} end",
]

def insert_junk(lua_code, chance=0.5):
    parts = [p.strip() for p in lua_code.split(';') if p.strip()]
    new_parts = []
    for part in parts:
        new_parts.append(part)
        if random.random() < chance:
            junk = random.choice(JUNK_TEMPLATES)
            label = random_name()
            if '{}' in junk:
                junk = junk.format(*(random_name() for _ in range(junk.count('{}'))))
            new_parts.append(junk)
    return ';'.join(new_parts)

def flatten_control_flow(lua_code):
    """Insert random goto jumps"""
    lines = lua_code.splitlines()
    new_lines = []
    for line in lines:
        if random.random() < 0.3:
            lbl = random_name()
            new_lines.append(f"::{lbl}::")
        new_lines.append(line)
        if random.random() < 0.3:
            lbl = random_name()
            new_lines.append(f"goto {lbl}")
    return '\n'.join(new_lines)

# ---------------------
# Top-level multi-layer loader
# ---------------------
def wrap_top_level(lua_code, xor_key=0x55, layers=2):
    for _ in range(layers):
        encrypted_bytes = xor_encrypt(lua_code.encode(), xor_key)
        encoded_str = encode_string_math(encrypted_bytes)
        dec_fn, dec_key, dec_res, dec_i = [random_name() for _ in range(4)]
        lua_code = (
            f"local function {dec_fn}({dec_res}) "
            f"local {dec_key}=''; "
            f"for {dec_i}=1,#({dec_res}) do "
            f"{dec_key}={dec_key}..string.char(string.byte({dec_res},{dec_i})~{xor_key}) "
            f"end return {dec_key} end; "
            f"loadstring({dec_fn}(string.char({encoded_str})))()"
        )
    return lua_code

# ---------------------
# Full obfuscation pipeline
# ---------------------
def obfuscate_lua(lua_code, xor_key=0x55):
    lua_code = rename_identifiers(lua_code)
    lua_code = encrypt_literals(lua_code, xor_key)
    lua_code = insert_junk(lua_code)
    lua_code = flatten_control_flow(lua_code)
    lua_code = wrap_top_level(lua_code, xor_key, layers=3)
    return lua_code

# ---------------------
# CLI
# ---------------------
def main():
    parser = argparse.ArgumentParser(description="Docksterling 3.0 - Luraph Mode Obfuscator")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("-k", "--key", type=int, default=0x55)
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print("Input file does not exist.")
        sys.exit(1)
    
    lua_code = args.input_file.read_text(encoding='utf-8')
    obf_code = obfuscate_lua(lua_code, args.key)
    
    if args.output:
        args.output.write_text(obf_code, encoding='utf-8')
        print(f"Obfuscated Lua saved to {args.output}")
    else:
        print(obf_code)

if __name__ == "__main__":
    main()
