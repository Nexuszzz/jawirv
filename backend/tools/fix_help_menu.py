#!/usr/bin/env python
"""Fix help menu in kicad_cli.py - add new sections"""
import re

filepath = "kicad/kicad_cli.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# New sections to add
new_sections = '''
{Colors.BOLD}📚 JOURNAL & RESEARCH (Auto Download!):{Colors.ENDC}
  {Colors.CYAN}/journal <query>{Colors.ENDC}    - 🔥 Search & DOWNLOAD jurnal dari arXiv!
  {Colors.CYAN}/download <url>{Colors.ENDC}     - Download file dari URL
  {Colors.CYAN}/interact <url> <task>{Colors.ENDC} - Browse & interact dengan AI
  
  Contoh:
  {Colors.GREEN}/journal Machine Learning IoT{Colors.ENDC}
  {Colors.GREEN}/journal Deep Learning Computer Vision{Colors.ENDC}
  {Colors.GREEN}/download https://arxiv.org/pdf/2301.00001.pdf{Colors.ENDC}
  {Colors.GREEN}/interact github.com find trending Python repos{Colors.ENDC}
  
  {Colors.DIM}Jurnal di-download otomatis ke folder: jawirv2/downloads/journals{Colors.ENDC}

{Colors.BOLD}🎬 YOUTUBE PLAY (Computer Use):{Colors.ENDC}
  {Colors.CYAN}/ytplay <query>{Colors.ENDC}     - 🔥 Search & PLAY video YouTube!
  {Colors.CYAN}/ytsearch <query>{Colors.ENDC}   - Search tanpa auto-play
  
  Contoh:
  {Colors.GREEN}/ytplay lofi hip hop music{Colors.ENDC}
  {Colors.GREEN}/ytplay tutorial arduino beginner{Colors.ENDC}
  
  {Colors.DIM}Browser terbuka, AI search & play video otomatis{Colors.ENDC}

'''

# Pattern to find the location (after Computer Use section, before FILE GENERATION)
pattern = r'(  \{Colors\.DIM\}Computer Use menggunakan Gemini Vision untuk "melihat" browser\s+dan melakukan aksi seperti manusia \(click, type, scroll, dll\)\{Colors\.ENDC\}\s*\n\n)(\{Colors\.BOLD\}.*FILE GENERATION)'

match = re.search(pattern, content)
if match:
    print(f"Found match at position {match.start()}")
    # Insert new sections between Computer Use and FILE GENERATION
    new_content = content[:match.end(1)] + new_sections + match.group(2) + content[match.end():]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Help menu updated successfully!")
else:
    # Try simpler pattern
    pattern2 = r'(scroll, dll\)\{Colors\.ENDC\}\s*\n\n)(\{Colors\.BOLD\}[^\n]*FILE)'
    match2 = re.search(pattern2, content)
    if match2:
        print(f"Found with pattern2 at position {match2.start()}")
        new_content = content[:match2.end(1)] + new_sections + match2.group(2) + content[match2.end():]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Help menu updated successfully!")
    else:
        print("❌ Pattern not found, trying another approach...")
        
        # Find FILE GENERATION in help section
        idx = content.find("FILE GENERATION:{Colors.ENDC}")
        if idx > 0:
            # Find the previous newline
            prev_newline = content.rfind('\n\n', 0, idx)
            if prev_newline > 0:
                print(f"Found FILE GENERATION at {idx}, prev_newline at {prev_newline}")
                new_content = content[:prev_newline+2] + new_sections + content[prev_newline+2:]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("✅ Help menu updated with fallback method!")
            else:
                print("❌ Could not find insertion point")
        else:
            print("❌ FILE GENERATION not found")
