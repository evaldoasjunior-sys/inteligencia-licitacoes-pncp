import cloudscraper
import json
import unicodedata
from datetime import datetime, timedelta

def remover_acentos(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def buscar_licitacoes_pncp(progresso_callback=None):
    with open('perfil_empresa.json', 'r', encoding='utf-8') as f:
        perfil = json.load(f)
    
    palavras_incluir = [remover_acentos(p) for p in perfil.get('palavras_chave', [])]
    palavras_excluir = [remover_acentos(p) for p in perfil.get('palavras_excluir', [])]
    
    termos_bloqueio_servico = [
        "prestacao de servico", "prestacao de servicos", "servico de", "servicos de",
        "manutencao", "locacao", "instalacao", "mao de obra", "reforma", "obra"
    ]
    todos_excluir = set(palavras_excluir + termos_bloqueio_servico)
    
    hoje = datetime.now()
    data_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
    
    resultados_totais = []
    ids_registrados = set()
    
    scraper = cloudscraper.create_scraper()
    
    # API de Contratações e Avisos de Licitação do Compras.gov.br
    url_compras = "https://compras.dados.gov.br/licitacoes/v1/licitacoes.json"
    
    if progresso_callback:
        progresso_callback(0.3, "Consultando API de Licitações do Compras.gov.br...")
        
    try:
        # Busca licitações abertas de fornecimento no Compras.gov.br
        params = {
            "data_publicacao_min": data_inicio
        }
        response = scraper.get(url_compras, params=params, timeout=20)
        
        if response.status_code == 200:
            dados = response.json()
            embedded = dados.get("_embedded", {})
            lista = embedded.get("licitacoes", [])
            
            if progresso_callback:
                progresso_callback(0.7, f"Filtrando {len(lista)} itens retornados do Compras.gov.br...")
                
            for item in lista:
                objeto_original = item.get("objeto", "") or ""
                objeto_limpo = remover_acentos(objeto_original)
                
                # Exclui serviços
                if any(e in objeto_limpo for e in todos_excluir):
                    continue
                
                # Filtra pelos termos do perfil da empresa
                if any(p in objeto_limpo for p in palavras_incluir) or not palavras_incluir:
                    uasg = item.get("uasg", "")
                    mod = item.get("codigo_modalidade", "")
                    num = item.get("numero_aviso", "")
                    id_unico = f"compras-{uasg}-{mod}-{num}"
                    
                    if id_unico not in ids_registrados:
                        ids_registrados.add(id_unico)
                        
                        orgao_nome = item.get("nome_uasg", "Órgão Compras.gov.br")
                        modalidade_nome = item.get("modalidade_licitacao", {}).get("descricao", "Pregão Eletrônico")
                        
                        oportunidade = {
                            "id": id_unico,
                            "orgao": orgao_nome,
                            "uf": item.get("uf", "BR"),
                            "municipio": item.get("municipio", ""),
                            "modalidade": modalidade_nome,
                            "objeto": objeto_original,
                            "valor_estimado": "Consulte o Edital",
                            "data_publicacao": str(item.get("data_publicacao", ""))[:10],
                            "link_oficial": f"https://www.comprasnet.gov.br/consultaLicitacoes/download/download_editais_detalhe.asp?coduasg={uasg}&modPrp={mod}&numprp={num}"
                        }
                        resultados_totais.append(oportunidade)
                        
    except Exception as e:
        print(f"Erro na conexão com Compras.gov.br: {str(e)}")
        
    if progresso_callback:
        progresso_callback(1.0, f"Coleta finalizada com {len(resultados_totais)} oportunidades encontradas!")

    with open('licitacoes_encontradas.json', 'w', encoding='utf-8') as f:
        json.dump(resultados_totais, f, ensure_ascii=False, indent=2)
        
    return resultados_totais