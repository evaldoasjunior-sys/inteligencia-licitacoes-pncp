import streamlit as st
import json
import os
from coletor_pncp import buscar_licitacoes_pncp

st.set_page_config(page_title="Inteligência em Licitações", page_icon="🛡️", layout="wide")

st.title("🛡️ Sistema de Inteligência em Licitações")
st.caption("Painel de Acompanhamento - Venda de Materiais (Lei 14.133/2021)")

# Botão para disparar a busca com feedback visual em tempo real
if st.button("🔄 Executar Nova Coleta Rápida no PNCP"):
    barra = st.progress(0)
    status_texto = st.empty()
    
    def atualizar_progresso(pct, texto):
        barra.progress(pct)
        status_texto.text(texto)

    dados = buscar_licitacoes_pncp(progresso_callback=atualizar_progresso)
    
    barra.progress(1.0)
    status_texto.success(f"Coleta concluída! {len(dados)} oportunidades de materiais encontradas.")
    st.rerun()

# Carrega os dados salvos
if os.path.exists('licitacoes_encontradas.json'):
    with open('licitacoes_encontradas.json', 'r', encoding='utf-8') as f:
        licitacoes = json.load(f)
else:
    licitacoes = []

st.subheader("📋 Oportunidades de Fornecimento de Materiais")
st.metric("Total de Oportunidades", len(licitacoes))

if licitacoes:
    estados = sorted(list(set([item['uf'] for item in licitacoes if item.get('uf')])))
    estado_selecionado = st.sidebar.selectbox("Filtrar por Estado (UF):", ["Todos"] + estados)

    st.markdown("---")
    
    for item in licitacoes:
        if estado_selecionado != "Todos" and item.get('uf') != estado_selecionado:
            continue
            
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {item['orgao']}")
                st.write(f"**Objeto:** {item['objeto']}")
                st.write(f"📍 **Local:** {item['municipio']} - {item['uf']} | **Modalidade:** {item['modalidade']}")
            
            with col2:
                st.write(f"💰 **Valor Estimado:**")
                st.subheader(f"R$ {item['valor_estimado']}")
                st.write(f"📅 **Publicação:** {item['data_publicacao']}")
                st.link_button("🔗 Ver no PNCP", item['link_oficial'])
                
        st.markdown("---")
else:
    st.info("Nenhuma oportunidade salva. Clique no botão acima para buscar no PNCP.")