#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import urllib.request
import urllib.error
from http.cookiejar import CookieJar
from html.parser import HTMLParser

class SefazParser(HTMLParser):
    def __init__(self, targets):
        super().__init__()
        # Aceita uma lista/set de alvos em maiúsculo
        self.targets = {t.upper().strip() for t in targets}
        self.in_table = False
        self.in_row = False
        self.in_col = False
        self.current_row_cols = []
        self.current_col_content = ""
        self.current_col_imgs = []
        self.found_rows = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table":
            tbl_id = attrs_dict.get("id", "")
            tbl_class = attrs_dict.get("class", "")
            if "gdvDisponibilidade" in tbl_id or "gdvDisponibilidade" in tbl_class or not tbl_id:
                self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row_cols = []
        elif (tag == "td" or tag == "th") and self.in_row:
            self.in_col = True
            self.current_col_content = ""
            self.current_col_imgs = []
        elif tag == "img" and self.in_col:
            src = attrs_dict.get("src", "")
            self.current_col_imgs.append(src)

    def handle_data(self, data):
        if self.in_col:
            self.current_col_content += data.strip()

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row_cols:
                col_text = self.current_row_cols[0]["text"].upper().strip()
                if col_text in self.targets:
                    self.found_rows[col_text] = self.current_row_cols
        elif (tag == "td" or tag == "th") and self.in_col:
            self.in_col = False
            self.current_row_cols.append({
                "text": self.current_col_content,
                "imgs": self.current_col_imgs
            })

def main():
    # Define o alvo padrão como "RS" se nenhum for fornecido
    arg_input = "RS"
    if len(sys.argv) > 1:
        arg_input = sys.argv[1]

    # Divide os alvos por vírgula para suportar múltiplos (ex: "RS,SVRS,SVC-RS")
    targets = [t.strip() for t in arg_input.split(",") if t.strip()]
    if not targets:
        targets = ["RS"]

    url = "https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with opener.open(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        parser = SefazParser(targets)
        parser.feed(html)
        
        # Verifica se pelo menos um dos alvos solicitados foi encontrado
        found_any = False
        has_issue = False
        
        for target in targets:
            target_upper = target.upper()
            if target_upper in parser.found_rows:
                found_any = True
                row_cols = parser.found_rows[target_upper]
                for col in row_cols:
                    for img in col["imgs"]:
                        if "amarela" in img or "vermelh" in img:
                            has_issue = True
                            break
                    if has_issue:
                        break
            if has_issue:
                break
                
        if not found_any:
            print(f"Error: Nenhum dos autorizadores {targets} foi encontrado na tabela.", file=sys.stderr)
            print("1")
            sys.exit(0)
            
        if has_issue:
            print("1")
        else:
            print("0")
            
    except Exception as e:
        print(f"Error fetching/parsing SEFAZ: {str(e)}", file=sys.stderr)
        # Em caso de erro de conexão, retorna 1 para acionar o alerta
        print("1")
        sys.exit(0)

if __name__ == "__main__":
    main()
