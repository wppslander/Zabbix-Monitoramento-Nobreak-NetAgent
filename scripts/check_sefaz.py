#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import urllib.request
import urllib.error
from http.cookiejar import CookieJar
from html.parser import HTMLParser

# Classe parser personalizada que herda de HTMLParser para analisar a estrutura HTML do portal da SEFAZ
class SefazParser(HTMLParser):
    def __init__(self, targets):
        super().__init__()
        # Converte todos os alvos solicitados para letras maiúsculas e remove espaços sobressalentes
        self.targets = {t.upper().strip() for t in targets}
        
        # Flags para controlar a posição do parser no documento HTML
        self.in_table = False
        self.in_row = False
        self.in_col = False
        
        # Estruturas de dados temporárias para coletar as colunas e imagens de cada linha
        self.current_row_cols = []
        self.current_col_content = ""
        self.current_col_imgs = []
        
        # Dicionário contendo os dados dos autorizadores encontrados (chave: nome do autorizador, valor: lista de colunas)
        self.found_rows = {}

    # Disparado quando o parser encontra uma tag de abertura (ex: <table>, <tr>, <td>, <img>)
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Identifica a tabela de disponibilidade dos serviços
        if tag == "table":
            tbl_id = attrs_dict.get("id", "")
            tbl_class = attrs_dict.get("class", "")
            # O portal usa uma GridView que geralmente possui "gdvDisponibilidade" no id/classe
            if "gdvDisponibilidade" in tbl_id or "gdvDisponibilidade" in tbl_class or not tbl_id:
                self.in_table = True
                
        # Entrou em uma linha da tabela
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row_cols = [] # Reinicia a lista de colunas para esta nova linha
            
        # Entrou em uma coluna (célula) da linha
        elif (tag == "td" or tag == "th") and self.in_row:
            self.in_col = True
            self.current_col_content = "" # Reinicia o conteúdo de texto da célula
            self.current_col_imgs = []    # Reinicia a lista de imagens dentro da célula
            
        # Se for uma imagem dentro da célula, armazena o caminho do arquivo de imagem (src)
        # O portal da SEFAZ usa imagens como bolinhas coloridas para representar o status
        elif tag == "img" and self.in_col:
            src = attrs_dict.get("src", "")
            self.current_col_imgs.append(src)

    # Disparado para extrair o texto interno de elementos (ex: o nome do estado na primeira coluna)
    def handle_data(self, data):
        if self.in_col:
            self.current_col_content += data.strip()

    # Disparado quando o parser encontra uma tag de fechamento (ex: </table>, </tr>, </td>)
    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
            
        # Ao fechar a linha, verifica se a primeira coluna corresponde a um dos nossos alvos de monitoramento
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row_cols:
                # O primeiro elemento da linha é sempre a sigla do estado/autorizador
                col_text = self.current_row_cols[0]["text"].upper().strip()
                if col_text in self.targets:
                    # Armazena a linha inteira para análise posterior
                    self.found_rows[col_text] = self.current_row_cols
                    
        # Ao fechar a coluna, salva seu texto e imagens coletadas no registro da linha
        elif (tag == "td" or tag == "th") and self.in_col:
            self.in_col = False
            self.current_row_cols.append({
                "text": self.current_col_content,
                "imgs": self.current_col_imgs
            })

def main():
    # Se nenhum autorizador for passado por argumento, define "RS" como padrão
    arg_input = "RS"
    if len(sys.argv) > 1:
        arg_input = sys.argv[1]

    # Divide os alvos passados por vírgula (ex: "RS,SVRS,SVC-RS") e remove espaços
    targets = [t.strip() for t in arg_input.split(",") if t.strip()]
    if not targets:
        targets = ["RS"]

    url = "https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx"
    
    # User-Agent simulando navegador real para evitar bloqueios automatizados ou erros da SEFAZ
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    # Cria um gerenciador de cookies (CookieJar). O portal da SEFAZ exige suporte a cookies
    # para aceitar a conexão (parâmetro AspxAutoDetectCookieSupport=1)
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(url, headers=headers)
    
    try:
        # Faz a requisição HTTP para o portal da SEFAZ com timeout de 15 segundos
        with opener.open(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        # Instancia e executa o parser HTML sobre o código retornado
        parser = SefazParser(targets)
        parser.feed(html)
        
        found_any = False
        has_issue = False
        
        # Itera sobre os autorizadores que o usuário pediu para verificar
        for target in targets:
            target_upper = target.upper()
            if target_upper in parser.found_rows:
                found_any = True
                row_cols = parser.found_rows[target_upper]
                
                # Itera sobre todas as colunas de serviços desse autorizador
                for col in row_cols:
                    for img in col["imgs"]:
                        # Verifica se alguma das imagens de status contém "amarela" (aviso) ou "vermelh" (erro)
                        # Imagens típicas: "bola_amarela_P.png" ou "bola_vermelho_P.png"
                        if "amarela" in img or "vermelh" in img:
                            has_issue = True
                            break
                    if has_issue:
                        break
            if has_issue:
                break
                
        # Se nenhum dos estados passados como argumento foi encontrado na tabela
        if not found_any:
            print(f"Error: Nenhum dos autorizadores {targets} foi encontrado na tabela de disponibilidade.", file=sys.stderr)
            print("1")
            sys.exit(0)
            
        # Retorna o resultado final na saída padrão (stdout):
        # 1 = Existe algum problema (instabilidade/offline)
        # 0 = Tudo funcionando perfeitamente (todas as bolinhas verdes)
        if has_issue:
            print("1")
        else:
            print("0")
            
    except Exception as e:
        # Se der erro de rede, timeout ou o portal estiver completamente fora do ar:
        # Imprime os detalhes do erro na saída de erro (stderr) e retorna 1 no stdout para acionar o alerta no Zabbix
        print(f"Error fetching/parsing SEFAZ: {str(e)}", file=sys.stderr)
        print("1")
        sys.exit(0)

if __name__ == "__main__":
    main()
