import os
import re
import json
from math import pow

# Simple WCAG contrast calculator utilities

def hex_to_rgb(h):
    h = h.strip()
    if h.startswith('rgb'):
        m = re.match(r'rgba?\(([^)]+)\)', h)
        if m:
            parts = [p.strip() for p in m.group(1).split(',')]
            r,g,b = [int(float(p)) for p in parts[:3]]
            return (r,g,b)
    if h.startswith('#'):
        h = h[1:]
    if len(h) == 3:
        r = int(h[0]*2, 16)
        g = int(h[1]*2, 16)
        b = int(h[2]*2, 16)
        return (r,g,b)
    if len(h) == 6:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return (r,g,b)
    return None


def srgb_to_lin(c):
    c = c/255.0
    if c <= 0.03928:
        return c/12.92
    return pow((c+0.055)/1.055, 2.4)


def luminance(rgb):
    r,g,b = rgb
    return 0.2126*srgb_to_lin(r) + 0.7152*srgb_to_lin(g) + 0.0722*srgb_to_lin(b)


def contrast_ratio(rgb1, rgb2):
    l1 = luminance(rgb1)
    l2 = luminance(rgb2)
    L1 = max(l1,l2)
    L2 = min(l1,l2)
    return (L1 + 0.05) / (L2 + 0.05)


# Find CSS variables declared in :root blocks across files
workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
var_map = {}
files_scanned = []

for root, dirs, files in os.walk(workspace):
    for fn in files:
        if fn.endswith('.html') or fn.endswith('.css'):
            path = os.path.join(root, fn)
            files_scanned.append(path)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    txt = f.read()
            except Exception:
                continue
            # find :root { ... }
            for m in re.finditer(r':root\s*\{([^}]+)\}', txt, re.S):
                body = m.group(1)
                for vm in re.finditer(r'--([a-zA-Z0-9-_]+)\s*:\s*([^;]+);', body):
                    name = vm.group(1).strip()
                    val = vm.group(2).strip()
                    var_map[name] = val

# Common token checks
tokens = ['text','bg','bg-alt','primary','primary-dark','secondary','accent','text-light','success','warning']
resolved = {}

for t in tokens:
    if t in var_map:
        resolved[t] = var_map[t]

# Helper to resolve var(...) and fallback

def resolve_value(val):
    val = val.strip()
    m = re.match(r'var\(--([a-zA-Z0-9-_]+)\)', val)
    if m:
        key = m.group(1)
        return var_map.get(key, None)
    return val

# Resolve and convert to rgb
rgb_map = {}
for k,v in resolved.items():
    rv = resolve_value(v)
    if rv:
        rgb = hex_to_rgb(rv)
        if rgb:
            rgb_map[k] = rgb

# Build pairs to test
pairs = []
if 'text' in rgb_map and 'bg' in rgb_map:
    pairs.append(('text','bg'))
if 'text' in rgb_map and 'bg-alt' in rgb_map:
    pairs.append(('text','bg-alt'))
if 'primary' in rgb_map:
    # primary on white and on secondary
    white = (255,255,255)
    pairs.append(('primary','white'))
    if 'secondary' in rgb_map:
        pairs.append(('primary','secondary'))
if 'accent' in rgb_map and 'bg' in rgb_map:
    pairs.append(('accent','bg'))
if 'text-light' in rgb_map and 'bg' in rgb_map:
    pairs.append(('text-light','bg'))
if 'success' in rgb_map and 'bg' in rgb_map:
    pairs.append(('success','bg'))

report = {
    'files_scanned_count': len(files_scanned),
    'variables_found': {k:var_map[k] for k in var_map},
    'resolved_rgb': {k: rgb_map[k] for k in rgb_map},
    'checks': []
}

for a,b in pairs:
    if a == 'white':
        rgb_a = (255,255,255)
    else:
        rgb_a = rgb_map.get(a)
    if b == 'white':
        rgb_b = (255,255,255)
    else:
        rgb_b = rgb_map.get(b)
    if rgb_a and rgb_b:
        ratio = contrast_ratio(rgb_a, rgb_b)
        pass_AA = ratio >= 4.5
        pass_AA_large = ratio >= 3.0
        pass_AAA = ratio >= 7.0
        report['checks'].append({
            'foreground': a,
            'background': b,
            'fg_rgb': rgb_a,
            'bg_rgb': rgb_b,
            'contrast_ratio': round(ratio, 2),
            'AA_normal_text': pass_AA,
            'AA_large_text': pass_AA_large,
            'AAA_normal_text': pass_AAA
        })

# Save report
out = os.path.join(workspace, 'contrast-report.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print('Contrast check complete. Report written to:', out)
print('Summary:')
for c in report['checks']:
    print(f"- {c['foreground']} on {c['background']}: ratio {c['contrast_ratio']} — AA: {c['AA_normal_text']}, AAA: {c['AAA_normal_text']}")

print('\nFound variables:')
for k,v in report['variables_found'].items():
    print(f"--{k}: {v}")
