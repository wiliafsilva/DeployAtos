import mysql.connector
import streamlit as st
import importlib

def conexaobanco():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="dudu2305",
            database="atoscapital"
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def validacao(usr, passw):
    conn = conexaobanco()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT u.*, g.codigo as grupo_codigo 
    FROM usuarios u
    LEFT JOIN grupoempresa g ON u.grupo_id = g.id
    WHERE u.usuario = %s AND u.senha = %s
    """
    cursor.execute(query, (usr, passw))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        st.session_state.authenticated = True  
        st.session_state.user_info = {
            'id': user['id'],
            'nome': user['Nome'],
            'permissao': user['permissao'],
            'grupo_id': user.get('grupo_id'),
            'grupo_codigo': user.get('grupo_codigo', '')
        }
        st.success('Login feito com sucesso!')

        if user['permissao'] == 'adm':
            st.session_state.page = "adm"
            st.rerun()
        elif user['permissao'] == 'cliente':
            if user.get('grupo_codigo'):
                codigo_grupo = user['grupo_codigo'].lower().strip()
                
                st.session_state.page = "dashboard"
                st.session_state.dashboard_page = f"pagina{codigo_grupo}"
                st.rerun()
            else:
                st.error('Usuário não está associado a nenhum grupo válido.')
        else:
            st.error('Permissão desconhecida. Não foi possível redirecionar.')
    else:
        st.error('Usuário ou senha incorretos, tente novamente.')

def arealogin():
    st.set_page_config(page_title="Login", page_icon="🔒", layout="centered")
    
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logoatos.png", width=150)

    with st.form('sign_in'):
        st.caption('Por favor, insira seu usuário e senha.')
        username = st.text_input('Usuário')
        password = st.text_input('Senha', type='password')

        botaoentrar = st.form_submit_button(label="Entrar", type="primary", use_container_width=True)

    if botaoentrar:
        validacao(username, password)

def carregar_pagina(nome_pagina):
    try:
        if nome_pagina == "dashboard":
            modulo = importlib.import_module("dashboard")
            pagina = st.session_state.get('dashboard_page', 'paginaatos')
            
            if hasattr(modulo, pagina):
                getattr(modulo, pagina)()
            else:
                st.error(f'Dashboard para este grupo não está disponível. Entre em contato com o suporte.')
                if st.button("Voltar"):
                    st.session_state.authenticated = False
                    st.session_state.page = None
                    st.rerun() 
        else:
            modulo = importlib.import_module(nome_pagina)
            if hasattr(modulo, f'pagina{nome_pagina}'):
                getattr(modulo, f'pagina{nome_pagina}')()
            else:
                st.error(f'Página {nome_pagina} não possui a função esperada')
    except ImportError as e:
        st.error(f'Erro ao carregar módulo: {e}')

def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        arealogin()
    else:
        if "page" in st.session_state:
            if st.session_state.page == "adm":
                carregar_pagina("adm")
            else:
                carregar_pagina(st.session_state.page)

if __name__ == "__main__":
    main()
