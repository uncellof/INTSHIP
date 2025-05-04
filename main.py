#импорт стандартных библиотек 3.11
import os
import json
import xml.etree.ElementTree as ET

def load_json(path):
    #загружаем JSON бд
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def merge_configs(base, patch):
    #объединяем конфиги
    out = base.copy()
    out.update(patch)
    return out

def compute_delta(base, patch):
    #ключи
    delta = {}
    for k, v in patch.items():
        if k not in base or base[k] != v:
            delta[k] = v
    return delta

def parse_xmi(xmi_file):
    #разбираем XMI и собраем классы
    tree = ET.parse(xmi_file)
    root = tree.getroot()
    classes = {}
    for cls in root.findall('Class'):
        name = cls.get('name')
        classes[name] = {
            'documentation': cls.get('documentation', ''),
            'is_root': cls.get('isRoot', 'false') == 'true',
            'attrs': [], 'associations': []
        }
    for cls in root.findall('Class'):
        for attr in cls.findall('Attribute'):
            classes[cls.get('name')]['attrs'].append({
                'name': attr.get('name'),
                'type': attr.get('type')
            })
    for agg in root.findall('Aggregation'):
        src = agg.get('source')
        tgt = agg.get('target')
        mult = agg.get('sourceMultiplicity', '1')
        if '..' in mult:
            lo, hi = mult.split('..', 1)
        else:
            lo = hi = mult
        if src in classes:
            classes[src]['associations'].append({
                'target': tgt, 'min': lo, 'max': hi
            })
    return classes

def write_config_xml(cfg, out_path):
    #сохраняем результат в файл config.xml
    root = ET.Element('BTS')
    def keyfn(item):
        k, _ = item
        return int(k.lstrip('param')) if k.startswith('param') else float('inf')
    for k, v in sorted(cfg.items(), key=keyfn):
        child = ET.SubElement(root, k)
        child.text = str(v)
    ET.ElementTree(root).write(out_path, encoding='utf-8', xml_declaration=True)

def write_meta_json(classes, out_path):
    #сохраняем результат в файл meta.json
    meta = []
    for name, info in classes.items():
        if info['is_root']:
            continue
        assoc = info['associations']
        entry = {
            'class': name,
            'documentation': info['documentation'],
            'isRoot': info['is_root'],
            'min': assoc[0]['min'] if assoc else None,
            'max': assoc[0]['max'] if assoc else None,
            'parameters': []
        }
        for a in info['attrs']:
            entry['parameters'].append({'name': a['name'], 'type': a['type']})
        for a in assoc:
            entry['parameters'].append({'name': a['target'], 'type': 'class'})
        meta.append(entry)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)

def main():
    base = os.path.dirname(__file__)
    inp = os.path.join(base, 'input')
    out = os.path.join(base, 'out')
    os.makedirs(out, exist_ok=True)

    #загружаем
    base_cfg = load_json(os.path.join(inp, 'config.json'))
    patch_cfg = load_json(os.path.join(inp, 'patched_config.json'))
    #объед и сохр патч
    cfg = merge_configs(base_cfg, patch_cfg)
    with open(os.path.join(out, 'res_patched_config.json'), 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    #выичсл и сохр дельту
    delta = compute_delta(base_cfg, patch_cfg)
    with open(os.path.join(out, 'delta.json'), 'w', encoding='utf-8') as f:
        json.dump(delta, f, indent=4, ensure_ascii=False)

    #парсимнх ХМЛ и вывод
    classes = parse_xmi(os.path.join(inp, 'impulse_test_input.xml'))
    write_config_xml(cfg, os.path.join(out, 'config.xml'))
    write_meta_json(classes, os.path.join(out, 'meta.json'))

if __name__ == '__main__':
    main()
