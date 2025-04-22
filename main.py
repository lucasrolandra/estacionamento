import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from database import *
import sqlite3
import win32print
import win32ui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from fpdf import FPDF
import os

class EstacionamentoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Estacionamento")
        self.root.geometry("1000x700")

        self.style = ttk.Style("flatly")
        
        self.criar_menu()
        self.criar_abas()
        self.criar_widgets()
        self.criar_relatorios_avancados()

    def criar_menu(self):
        menubar = tk.Menu(self.root)
        
        # Menu Arquivo
        menu_arquivo = tk.Menu(menubar, tearoff=0)
        menu_arquivo.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=menu_arquivo)
        
        # Menu Relatórios
        menu_relatorios = tk.Menu(menubar, tearoff=0)
        menu_relatorios.add_command(label="Diário", command=self.gerar_relatorio_diario)
        menu_relatorios.add_command(label="Mensal", command=self.gerar_relatorio_mensal)
        menu_relatorios.add_command(label="Personalizado", command=self.abrir_filtro_datas)
        menubar.add_cascade(label="Relatórios", menu=menu_relatorios)
        
        self.root.config(menu=menubar)

    def criar_abas(self):
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        
        # Criar todas as abas
        self.aba_dashboard = ttk.Frame(self.notebook)
        self.aba_veiculos = ttk.Frame(self.notebook)
        self.aba_cadastro = ttk.Frame(self.notebook)
        self.aba_entrada = ttk.Frame(self.notebook)
        self.aba_saida = ttk.Frame(self.notebook)
        self.aba_estacionados = ttk.Frame(self.notebook)
        self.aba_relatorios = ttk.Frame(self.notebook)
        
        # Adicionar abas ao notebook
        self.notebook.add(self.aba_dashboard, text="Dashboard")
        self.notebook.add(self.aba_veiculos, text="Veículos")
        self.notebook.add(self.aba_cadastro, text="Cadastro")
        self.notebook.add(self.aba_entrada, text="Entrada")
        self.notebook.add(self.aba_saida, text="Saída")
        self.notebook.add(self.aba_estacionados, text="Estacionados")
        self.notebook.add(self.aba_relatorios, text="Relatórios Avançados")
        
        self.notebook.pack(expand=True, fill="both")

    def criar_dashboard(self):
        hoje = date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect("estacionamento.db")
        cursor = conn.cursor()
        
        # Consultas para o dashboard
        cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE date(entrada) = date(?)", (hoje,))
        total_entradas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE date(saida) = date(?)", (hoje,))
        total_saidas = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(valor_pago) FROM movimentacoes WHERE date(saida) = date(?)", (hoje,))
        valor_total = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE saida IS NULL")
        estacionados = cursor.fetchone()[0]
        
        conn.close()

        # Layout do dashboard
        frame = ttk.Frame(self.aba_dashboard, padding=30)
        frame.pack(expand=True)

        ttk.Label(frame, text="Resumo do Dia", font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))

        # Cartões de informação
        card1 = ttk.LabelFrame(frame, text="Entradas Hoje", bootstyle="info")
        ttk.Label(card1, text=f"{total_entradas}", font=("Segoe UI", 24)).pack(pady=10)
        card1.pack(side="left", expand=True, fill="both", padx=5, pady=5)

        card2 = ttk.LabelFrame(frame, text="Saídas Hoje", bootstyle="success")
        ttk.Label(card2, text=f"{total_saidas}", font=("Segoe UI", 24)).pack(pady=10)
        card2.pack(side="left", expand=True, fill="both", padx=5, pady=5)

        card3 = ttk.LabelFrame(frame, text="Faturamento", bootstyle="warning")
        ttk.Label(card3, text=f"R$ {valor_total:.2f}", font=("Segoe UI", 24)).pack(pady=10)
        card3.pack(side="left", expand=True, fill="both", padx=5, pady=5)

        card4 = ttk.LabelFrame(frame, text="Estacionados", bootstyle="danger")
        ttk.Label(card4, text=f"{estacionados}", font=("Segoe UI", 24)).pack(pady=10)
        card4.pack(side="left", expand=True, fill="both", padx=5, pady=5)

    def criar_tela_veiculos(self):
        # Treeview para listar veículos
        self.tree_veiculos = ttk.Treeview(
            self.aba_veiculos, 
            columns=("Placa", "Modelo", "Cor", "Tipo", "Proprietário"), 
            show="headings", 
            bootstyle="secondary"
        )
        
        # Configurar colunas
        colunas = ["Placa", "Modelo", "Cor", "Tipo", "Proprietário"]
        for col in colunas:
            self.tree_veiculos.heading(col, text=col)
            self.tree_veiculos.column(col, anchor="center", width=120)
        
        self.tree_veiculos.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Frame para botões
        btn_frame = ttk.Frame(self.aba_veiculos)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Editar", 
            command=self.editar_veiculo, 
            bootstyle="warning"
        ).grid(row=0, column=0, padx=10)
        
        ttk.Button(
            btn_frame, 
            text="Excluir", 
            command=self.excluir_veiculo, 
            bootstyle="danger"
        ).grid(row=0, column=1, padx=10)
        
        self.atualizar_veiculos()

    def atualizar_veiculos(self):
        # Limpar treeview
        for i in self.tree_veiculos.get_children():
            self.tree_veiculos.delete(i)
        
        # Buscar veículos no banco
        conn = sqlite3.connect("estacionamento.db")
        cursor = conn.cursor()
        cursor.execute("SELECT placa, modelo, cor, tipo, proprietario FROM veiculos")
        
        # Adicionar veículos ao treeview
        for v in cursor.fetchall():
            self.tree_veiculos.insert("", tk.END, values=v)
        
        conn.close()

    def editar_veiculo(self):
        item = self.tree_veiculos.selection()
        if not item:
            messagebox.showwarning("Aviso", "Selecione um veículo para editar.")
            return
            
        dados = self.tree_veiculos.item(item, "values")
        
        # Janela de edição
        janela = ttk.Toplevel(self.root)
        janela.title("Editar Veículo")
        janela.geometry("350x300")
        
        # Variáveis para os campos
        vars = [tk.StringVar(value=dados[i]) for i in range(5)]
        labels = ["Placa", "Modelo", "Cor", "Tipo", "Proprietário"]
        
        # Criar campos de edição
        for i, texto in enumerate(labels):
            ttk.Label(janela, text=texto).pack(pady=2)
            
            if i == 3:  # Campo tipo como Combobox
                tipo_entry = ttk.Combobox(
                    janela, 
                    textvariable=vars[i], 
                    values=["Carro", "Moto", "Caminhão", "Outro"]
                )
                tipo_entry.pack(pady=2)
            else:
                ttk.Entry(janela, textvariable=vars[i]).pack(pady=2)
        
        # Botão salvar
        def salvar():
            conn = sqlite3.connect("estacionamento.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE veiculos SET modelo=?, cor=?, tipo=?, proprietario=? WHERE placa=?", 
                (vars[1].get(), vars[2].get(), vars[3].get(), vars[4].get(), vars[0].get())
            )
            conn.commit()
            conn.close()
            self.atualizar_veiculos()
            janela.destroy()
        
        ttk.Button(
            janela, 
            text="Salvar", 
            command=salvar, 
            bootstyle="success"
        ).pack(pady=10)

    def excluir_veiculo(self):
        item = self.tree_veiculos.selection()
        if not item:
            messagebox.showwarning("Aviso", "Selecione um veículo para excluir.")
            return
            
        placa = self.tree_veiculos.item(item, "values")[0]
        
        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja excluir o veículo {placa}?"):
            conn = sqlite3.connect("estacionamento.db")
            cursor = conn.cursor()
            
            # Verificar se existem movimentações
            cursor.execute(
                "SELECT COUNT(*) FROM movimentacoes m JOIN veiculos v ON v.id = m.veiculo_id WHERE v.placa=?", 
                (placa,)
            )
            
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro", "Este veículo possui movimentações e não pode ser excluído.")
                conn.close()
                return
                
            cursor.execute("DELETE FROM veiculos WHERE placa=?", (placa,))
            conn.commit()
            conn.close()
            self.atualizar_veiculos()

    def criar_widgets(self):
        self.criar_dashboard()
        self.criar_tela_veiculos()

        # Funções auxiliares para criação de widgets
        def label(frame, text, row):
            ttk.Label(
                frame, 
                text=text, 
                font=("Segoe UI", 11)
            ).grid(row=row, column=0, padx=10, pady=8, sticky="e")

        def entry(frame, var, row):
            ent = ttk.Entry(
                frame, 
                textvariable=var, 
                font=("Segoe UI", 11), 
                width=30
            )
            ent.grid(row=row, column=1, padx=10, pady=8)
            ent.bind("<KeyRelease>", self.forcar_maiusculas)
            return ent

        # Aba de Cadastro
        self.placa_var = tk.StringVar()
        self.modelo_var = tk.StringVar()
        self.cor_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="Carro")
        self.prop_var = tk.StringVar()

        label(self.aba_cadastro, "Placa:", 0)
        label(self.aba_cadastro, "Modelo:", 1)
        label(self.aba_cadastro, "Cor:", 2)
        label(self.aba_cadastro, "Tipo:", 3)
        label(self.aba_cadastro, "Proprietário:", 4)

        self.placa_entry = entry(self.aba_cadastro, self.placa_var, 0)
        self.modelo_entry = entry(self.aba_cadastro, self.modelo_var, 1)
        self.cor_entry = entry(self.aba_cadastro, self.cor_var, 2)
        
        # Combobox para tipo
        self.tipo_entry = ttk.Combobox(
            self.aba_cadastro, 
            textvariable=self.tipo_var, 
            values=["Carro", "Moto", "Caminhão", "Outro"], 
            state="readonly"
        )
        self.tipo_entry.grid(row=3, column=1, padx=10, pady=8, sticky="w")
        
        self.proprietario_entry = entry(self.aba_cadastro, self.prop_var, 4)

        ttk.Button(
            self.aba_cadastro, 
            text="Cadastrar Veículo", 
            command=self.cadastrar_veiculo, 
            bootstyle="success"
        ).grid(row=5, column=0, columnspan=2, pady=15)

        # Aba de Entrada
        self.entrada_var = tk.StringVar()
        label(self.aba_entrada, "Placa:", 0)
        self.entrada_placa_entry = entry(self.aba_entrada, self.entrada_var, 0)
        
        ttk.Button(
            self.aba_entrada, 
            text="Registrar Entrada", 
            command=self.registrar_entrada, 
            bootstyle="primary"
        ).grid(row=1, column=0, columnspan=2, pady=15)

        # Aba de Saída
        self.saida_var = tk.StringVar()
        self.valor_hora = tk.StringVar(value="5.00")
        
        label(self.aba_saida, "Placa:", 0)
        self.saida_placa_entry = entry(self.aba_saida, self.saida_var, 0)
        
        label(self.aba_saida, "Valor por hora:", 1)
        self.valor_hora_entry = entry(self.aba_saida, self.valor_hora, 1)
        
        ttk.Button(
            self.aba_saida, 
            text="Registrar Saída", 
            command=self.registrar_saida, 
            bootstyle="warning"
        ).grid(row=2, column=0, columnspan=2, pady=15)

        # Aba de Estacionados
        self.tree_estacionados = ttk.Treeview(
            self.aba_estacionados, 
            columns=("Placa", "Modelo", "Tipo", "Entrada"), 
            show="headings", 
            bootstyle="info"
        )
        
        for col in self.tree_estacionados["columns"]:
            self.tree_estacionados.heading(col, text=col)
            self.tree_estacionados.column(col, anchor="center")
        
        self.tree_estacionados.pack(expand=True, fill="both", padx=10, pady=10)
        
        ttk.Button(
            self.aba_estacionados, 
            text="Atualizar Lista", 
            command=self.atualizar_estacionados, 
            bootstyle="primary"
        ).pack(pady=5)
        
        self.atualizar_estacionados()

    def criar_relatorios_avancados(self):
        """Adiciona uma nova aba para relatórios avançados"""
        # Frame de filtros
        filtro_frame = ttk.LabelFrame(self.aba_relatorios, text="Filtros", padding=10)
        filtro_frame.pack(fill="x", padx=10, pady=5)
        
        # Período
        ttk.Label(filtro_frame, text="Período:").grid(row=0, column=0, sticky="e")
        self.relatorio_data_inicio = ttk.Entry(filtro_frame, width=12)
        self.relatorio_data_inicio.grid(row=0, column=1, padx=5)
        ttk.Label(filtro_frame, text="até").grid(row=0, column=2)
        self.relatorio_data_fim = ttk.Entry(filtro_frame, width=12)
        self.relatorio_data_fim.grid(row=0, column=3, padx=5)
        
        # Tipo de veículo
        ttk.Label(filtro_frame, text="Tipo:").grid(row=0, column=4, sticky="e", padx=(10,0))
        self.relatorio_tipo = ttk.Combobox(filtro_frame, values=["Todos", "Carro", "Moto", "Caminhão"], width=8)
        self.relatorio_tipo.grid(row=0, column=5)
        self.relatorio_tipo.current(0)
        
        # Botões
        btn_frame = ttk.Frame(filtro_frame)
        btn_frame.grid(row=0, column=6, padx=10)
        ttk.Button(
            btn_frame, 
            text="Aplicar", 
            command=self.atualizar_relatorios, 
            bootstyle="primary"
        ).pack(side="left", padx=2)
        
        ttk.Button(
            btn_frame, 
            text="Exportar PDF", 
            command=self.exportar_pdf, 
            bootstyle="secondary"
        ).pack(side="left", padx=2)
        
        ttk.Button(
            btn_frame, 
            text="Exportar Excel", 
            command=self.exportar_excel, 
            bootstyle="secondary"
        ).pack(side="left", padx=2)
        
        # Área de visualização
        view_frame = ttk.Frame(self.aba_relatorios)
        view_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Notebook para os diferentes relatórios
        self.relatorio_notebook = ttk.Notebook(view_frame)
        self.relatorio_notebook.pack(fill="both", expand=True)
        
        # Aba de dados tabulares
        self.aba_dados = ttk.Frame(self.relatorio_notebook)
        self.relatorio_notebook.add(self.aba_dados, text="Dados")
        
        self.tree_relatorio = ttk.Treeview(
            self.aba_dados, 
            columns=("Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"), 
            show="headings", 
            bootstyle="info"
        )
        
        for col in self.tree_relatorio["columns"]:
            self.tree_relatorio.heading(col, text=col)
            self.tree_relatorio.column(col, anchor="center", width=100)
        
        self.tree_relatorio.pack(fill="both", expand=True)
        
        # Aba de gráficos
        self.aba_graficos = ttk.Frame(self.relatorio_notebook)
        self.relatorio_notebook.add(self.aba_graficos, text="Gráficos")
        
        # Frame para os gráficos
        self.graficos_frame = ttk.Frame(self.aba_graficos)
        self.graficos_frame.pack(fill="both", expand=True)
        
        # Definir datas padrão (últimos 7 dias)
        hoje = datetime.now().strftime("%d/%m/%Y")
        sete_dias_atras = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
        self.relatorio_data_inicio.insert(0, sete_dias_atras)
        self.relatorio_data_fim.insert(0, hoje)
        
        # Carregar dados iniciais
        self.atualizar_relatorios()

    def forcar_maiusculas(self, event):
        widget = event.widget
        texto = widget.get()
        widget.delete(0, tk.END)
        widget.insert(0, texto.upper())

    def cadastrar_veiculo(self):
        if all([self.placa_var.get(), self.modelo_var.get(), self.cor_var.get(), self.prop_var.get()]):
            if cadastrar_veiculo(
                self.placa_var.get(), 
                self.modelo_var.get(), 
                self.cor_var.get(), 
                self.tipo_var.get(),
                self.prop_var.get()
            ):
                messagebox.showinfo("Sucesso", "Veículo cadastrado com sucesso!")
                # Limpar campos
                self.placa_var.set("")
                self.modelo_var.set("")
                self.cor_var.set("")
                self.tipo_var.set("Carro")
                self.prop_var.set("")
            else:
                messagebox.showerror("Erro", "Erro ao cadastrar veículo. Verifique se a placa já existe.")
        else:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")

    def registrar_entrada(self):
        placa = self.entrada_var.get()
        if not placa:
            messagebox.showwarning("Aviso", "Informe a placa do veículo.")
            return
            
        if registrar_entrada(placa):
            veiculo = self.buscar_veiculo_por_placa(placa)
            if veiculo:
                self.imprimir_ticket("ENTRADA", placa, *veiculo)
                messagebox.showinfo("Sucesso", f"Entrada de {placa} registrada.")
                self.entrada_var.set("")
                self.atualizar_estacionados()
                self.atualizar_dashboard()
            else:
                messagebox.showerror("Erro", "Veículo não encontrado no cadastro.")
        else:
            messagebox.showerror("Erro", "Erro ao registrar entrada ou veículo já está estacionado.")

    def registrar_saida(self):
        placa = self.saida_var.get()
        if not placa:
            messagebox.showwarning("Aviso", "Informe a placa do veículo.")
            return
            
        try:
            valor = float(self.valor_hora.get())
            total = registrar_saida(placa, valor)
            if total is not None:
                self.imprimir_ticket("SAÍDA", placa, valor_pago=total)
                messagebox.showinfo("Saída registrada", f"Valor: R$ {total:.2f}")
                self.saida_var.set("")
                self.atualizar_estacionados()
                self.atualizar_dashboard()
            else:
                messagebox.showerror("Erro", "Veículo não encontrado ou não está estacionado.")
        except ValueError:
            messagebox.showerror("Erro", "Valor por hora inválido.")

    def atualizar_estacionados(self):
        for i in self.tree_estacionados.get_children():
            self.tree_estacionados.delete(i)
            
        for v in listar_veiculos_estacionados():
            entrada_formatada = datetime.strptime(v[3], '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m %H:%M')
            self.tree_estacionados.insert("", tk.END, values=(v[0], v[1], v[2], entrada_formatada))

    def atualizar_dashboard(self):
        # Remove o frame antigo e cria um novo
        for widget in self.aba_dashboard.winfo_children():
            widget.destroy()
        self.criar_dashboard()

    def buscar_veiculo_por_placa(self, placa):
        conn = sqlite3.connect('estacionamento.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT modelo, cor, tipo, proprietario FROM veiculos WHERE placa = ?", 
            (placa,)
        )
        v = cursor.fetchone()
        conn.close()
        return v

    def imprimir_ticket(self, tipo, placa, modelo="", cor="", tipo_veiculo="", proprietario="", valor_pago=None):
        linhas = [f"TICKET DE {tipo}", f"Placa: {placa}"]
        
        if tipo == "ENTRADA":
            linhas += [
                f"Modelo: {modelo}", 
                f"Cor: {cor}", 
                f"Tipo: {tipo_veiculo}",
                f"Proprietário: {proprietario}"
            ]
        
        if tipo == "SAÍDA" and valor_pago is not None:
            linhas.append(f"Valor Pago: R$ {valor_pago:.2f}")
        
        linhas.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        try:
            pdc = win32ui.CreateDC()
            pdc.CreatePrinterDC(win32print.GetDefaultPrinter())
            pdc.StartDoc(f"Ticket {tipo}")
            pdc.StartPage()
            
            x, y, dy = 100, 100, 150
            for linha in linhas:
                pdc.TextOut(x, y, linha)
                y += dy
                
            pdc.EndPage()
            pdc.EndDoc()
            pdc.DeleteDC()
        except Exception as e:
            messagebox.showerror("Erro de Impressão", f"Não foi possível imprimir o ticket: {str(e)}")

    def gerar_relatorio_diario(self):
        hoje = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect('estacionamento.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT v.placa, v.tipo, m.entrada, m.saida, 
               (julianday(m.saida) - julianday(m.entrada)) * 24 as horas,
               m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        WHERE date(m.entrada) = date(?)
        ''', (hoje,))
        dados = cursor.fetchall()
        conn.close()
        self.mostrar_relatorio(dados, f"Relatório Diário - {datetime.now().strftime('%d/%m/%Y')}")

    def gerar_relatorio_mensal(self):
        mes_atual = datetime.now().strftime('%Y-%m')
        conn = sqlite3.connect('estacionamento.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT v.placa, v.tipo, m.entrada, m.saida, 
               (julianday(m.saida) - julianday(m.entrada)) * 24 as horas,
               m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        WHERE strftime('%Y-%m', m.entrada) = ?
        ''', (mes_atual,))
        dados = cursor.fetchall()
        conn.close()
        self.mostrar_relatorio(dados, f"Relatório Mensal - {datetime.now().strftime('%m/%Y')}")

    def abrir_filtro_datas(self):
        janela = ttk.Toplevel(self.root)
        janela.title("Relatório por Datas")
        janela.geometry("300x150")
        
        ttk.Label(janela, text="Data Inicial (DD/MM/AAAA):").pack(pady=5)
        data_inicio_entry = ttk.Entry(janela)
        data_inicio_entry.pack()
        
        ttk.Label(janela, text="Data Final (DD/MM/AAAA):").pack(pady=5)
        data_fim_entry = ttk.Entry(janela)
        data_fim_entry.pack()

        def gerar():
            try:
                d1 = datetime.strptime(data_inicio_entry.get(), "%d/%m/%Y")
                d2 = datetime.strptime(data_fim_entry.get(), "%d/%m/%Y")
                relatorio = self.gerar_relatorio_intervalo(d1, d2)
                self.mostrar_relatorio(relatorio, f"Relatório de {data_inicio_entry.get()} a {data_fim_entry.get()}")
                janela.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/AAAA.")

        ttk.Button(janela, text="Gerar", command=gerar, bootstyle="primary").pack(pady=10)

    def gerar_relatorio_intervalo(self, d1, d2):
        conn = sqlite3.connect('estacionamento.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT v.placa, v.tipo, m.entrada, m.saida, 
               (julianday(m.saida) - julianday(m.entrada)) * 24 as horas,
               m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        WHERE date(m.entrada) BETWEEN date(?) AND date(?)
        ''', (d1.strftime('%Y-%m-%d'), d2.strftime('%Y-%m-%d')))
        dados = cursor.fetchall()
        conn.close()
        return dados

    def mostrar_relatorio(self, relatorio, titulo):
        janela = ttk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("900x500")
        
        tree = ttk.Treeview(
            janela, 
            columns=("Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"), 
            show="headings", 
            bootstyle="info"
        )
        
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")
        
        for item in relatorio:
            entrada = datetime.strptime(item[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M")
            saida = datetime.strptime(item[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M") if item[3] else "-"
            horas = f"{float(item[4]):.1f}h" if item[4] else "-"
            valor = f"R$ {float(item[5]):.2f}" if item[5] else "-"
            
            tree.insert("", tk.END, values=(item[0], item[1], entrada, saida, horas, valor))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Adicionar botão de exportação
        btn_frame = ttk.Frame(janela)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame, 
            text="Exportar para PDF", 
            command=lambda: self.exportar_relatorio_pdf(relatorio, titulo), 
            bootstyle="secondary"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Exportar para Excel", 
            command=lambda: self.exportar_relatorio_excel(relatorio, titulo), 
            bootstyle="secondary"
        ).pack(side="left", padx=5)

    def atualizar_relatorios(self):
        """Atualiza todos os relatórios com base nos filtros"""
        try:
            data_inicio = datetime.strptime(self.relatorio_data_inicio.get(), "%d/%m/%Y")
            data_fim = datetime.strptime(self.relatorio_data_fim.get(), "%d/%m/%Y")
            tipo = self.relatorio_tipo.get()
            
            # Obter dados do banco
            dados = self.obter_dados_relatorio(data_inicio, data_fim, tipo)
            
            # Atualizar tabela
            self.atualizar_tabela_relatorio(dados)
            
            # Atualizar gráficos
            self.atualizar_graficos(dados, data_inicio, data_fim)
            
        except ValueError as e:
            messagebox.showerror("Erro", "Data inválida! Use o formato DD/MM/AAAA")

    def obter_dados_relatorio(self, data_inicio, data_fim, tipo="Todos"):
        """Obtém os dados do banco com base nos filtros"""
        conn = sqlite3.connect("estacionamento.db")
        query = """
        SELECT v.placa, v.tipo, m.entrada, m.saida, 
               (julianday(m.saida) - julianday(m.entrada)) * 24 as horas,
               m.valor_pago
        FROM veiculos v
        JOIN movimentacoes m ON v.id = m.veiculo_id
        WHERE date(m.entrada) BETWEEN ? AND ?
        """
        params = [data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")]
        
        if tipo != "Todos":
            query += " AND v.tipo = ?"
            params.append(tipo)
            
        query += " ORDER BY m.entrada DESC"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def atualizar_tabela_relatorio(self, dados):
        """Atualiza a tabela com os dados do relatório"""
        for item in self.tree_relatorio.get_children():
            self.tree_relatorio.delete(item)
            
        for row in dados:
            entrada = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M")
            saida = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M") if row[3] else "-"
            horas = f"{float(row[4]):.1f}h" if row[4] else "-"
            valor = f"R$ {float(row[5]):.2f}" if row[5] else "-"
            
            self.tree_relatorio.insert("", "end", values=(row[0], row[1], entrada, saida, horas, valor))

    def atualizar_graficos(self, dados, data_inicio, data_fim):
        """Atualiza os gráficos com os dados do relatório"""
        # Limpa frame anterior
        for widget in self.graficos_frame.winfo_children():
            widget.destroy()
            
        if not dados:
            ttk.Label(self.graficos_frame, text="Nenhum dado encontrado para o período selecionado").pack(pady=50)
            return
            
        # Converter para DataFrame para facilitar
        df = pd.DataFrame(dados, columns=["placa", "tipo", "entrada", "saida", "horas", "valor"])
        df['entrada'] = pd.to_datetime(df['entrada'])
        df['dia'] = df['entrada'].dt.date
        
        # Criar figura com subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10))
        fig.tight_layout(pad=3.0)
        
        # Gráfico 1: Faturamento por dia
        faturamento_dia = df.groupby('dia')['valor'].sum()
        ax1.bar(faturamento_dia.index.astype(str), faturamento_dia)
        ax1.set_title(f"Faturamento por Dia ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})")
        ax1.set_ylabel("Valor (R$)")
        ax1.tick_params(axis='x', rotation=45)
        
        # Gráfico 2: Veículos por tipo
        if 'tipo' in df.columns:
            tipos = df['tipo'].value_counts()
            ax2.pie(tipos, labels=tipos.index, autopct='%1.1f%%')
            ax2.set_title("Distribuição por Tipo de Veículo")
        
        # Gráfico 3: Média de horas estacionadas
        if 'horas' in df.columns:
            media_horas = df.groupby('dia')['horas'].mean()
            ax3.plot(media_horas.index.astype(str), media_horas, marker='o')
            ax3.set_title("Média de Horas Estacionadas por Dia")
            ax3.set_ylabel("Horas")
            ax3.tick_params(axis='x', rotation=45)
        
        # Embedar os gráficos na interface
        canvas = FigureCanvasTkAgg(fig, master=self.graficos_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def exportar_pdf(self):
        """Exporta o relatório atual para PDF"""
        try:
            data_inicio = datetime.strptime(self.relatorio_data_inicio.get(), "%d/%m/%Y")
            data_fim = datetime.strptime(self.relatorio_data_fim.get(), "%d/%m/%Y")
            tipo = self.relatorio_tipo.get()
            
            # Obter dados
            dados = self.obter_dados_relatorio(data_inicio, data_fim, tipo)
            
            if not dados:
                messagebox.showwarning("Aviso", "Nenhum dado para exportar!")
                return
                
            # Criar nome do arquivo
            nome_arquivo = f"relatorio_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}"
            if tipo != "Todos":
                nome_arquivo += f"_{tipo.lower()}"
            nome_arquivo += ".pdf"
            
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", nome_arquivo)
            
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Título
            titulo = f"Relatório de Estacionamento - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            if tipo != "Todos":
                titulo += f" - Tipo: {tipo}"
                
            pdf.cell(200, 10, txt=titulo, ln=1, align="C")
            pdf.ln(10)
            
            # Tabela
            col_widths = [30, 25, 35, 35, 20, 25]
            headers = ["Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"]
            
            # Cabeçalho
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, txt=header, border=1)
            pdf.ln()
            
            # Dados
            for row in dados:
                entrada = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M")
                saida = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M") if row[3] else "-"
                horas = f"{float(row[4]):.1f}h" if row[4] else "-"
                valor = f"R$ {float(row[5]):.2f}" if row[5] else "-"
                
                pdf.cell(col_widths[0], 10, txt=row[0], border=1)
                pdf.cell(col_widths[1], 10, txt=row[1], border=1)
                pdf.cell(col_widths[2], 10, txt=entrada, border=1)
                pdf.cell(col_widths[3], 10, txt=saida, border=1)
                pdf.cell(col_widths[4], 10, txt=horas, border=1)
                pdf.cell(col_widths[5], 10, txt=valor, border=1)
                pdf.ln()
            
            # Totais
            pdf.ln(5)
            total_veiculos = len(dados)
            total_valor = sum(float(row[5]) for row in dados if row[5])
            pdf.cell(0, 10, txt=f"Total de Veículos: {total_veiculos}", ln=1)
            pdf.cell(0, 10, txt=f"Faturamento Total: R$ {total_valor:.2f}", ln=1)
            
            # Salvar arquivo
            pdf.output(file_path)
            
            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar PDF:\n{str(e)}")

    def exportar_excel(self):
        """Exporta o relatório atual para Excel"""
        try:
            data_inicio = datetime.strptime(self.relatorio_data_inicio.get(), "%d/%m/%Y")
            data_fim = datetime.strptime(self.relatorio_data_fim.get(), "%d/%m/%Y")
            tipo = self.relatorio_tipo.get()
            
            # Obter dados
            dados = self.obter_dados_relatorio(data_inicio, data_fim, tipo)
            
            if not dados:
                messagebox.showwarning("Aviso", "Nenhum dado para exportar!")
                return
                
            # Criar DataFrame
            df = pd.DataFrame(dados, columns=["Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"])
            
            # Formatar colunas de data/hora
            df['Entrada'] = pd.to_datetime(df['Entrada']).dt.strftime('%d/%m/%Y %H:%M')
            df['Saída'] = pd.to_datetime(df['Saída']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Calcular totais
            total_veiculos = len(df)
            total_valor = df['Valor'].sum()
            
            # Criar nome do arquivo
            nome_arquivo = f"relatorio_{data_inicio.strftime('%Y%m%d')}_{data_fim.strftime('%Y%m%d')}"
            if tipo != "Todos":
                nome_arquivo += f"_{tipo.lower()}"
            nome_arquivo += ".xlsx"
            
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", nome_arquivo)
            
            # Criar arquivo Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Movimentações', index=False)
                
                # Adicionar resumo
                resumo = pd.DataFrame({
                    'Métrica': ['Período', 'Tipo', 'Total Veículos', 'Faturamento Total'],
                    'Valor': [
                        f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
                        tipo,
                        total_veiculos,
                        f"R$ {total_valor:.2f}"
                    ]
                })
                resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar Excel:\n{str(e)}")

    def exportar_relatorio_pdf(self, relatorio, titulo):
        """Exporta um relatório específico para PDF"""
        try:
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Título
            pdf.cell(200, 10, txt=titulo, ln=1, align="C")
            pdf.ln(10)
            
            # Tabela
            col_widths = [30, 25, 35, 35, 20, 25]
            headers = ["Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"]
            
            # Cabeçalho
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, txt=header, border=1)
            pdf.ln()
            
            # Dados
            for row in relatorio:
                entrada = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M")
                saida = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S.%f").strftime("%d/%m %H:%M") if row[3] else "-"
                horas = f"{float(row[4]):.1f}h" if row[4] else "-"
                valor = f"R$ {float(row[5]):.2f}" if row[5] else "-"
                
                pdf.cell(col_widths[0], 10, txt=row[0], border=1)
                pdf.cell(col_widths[1], 10, txt=row[1], border=1)
                pdf.cell(col_widths[2], 10, txt=entrada, border=1)
                pdf.cell(col_widths[3], 10, txt=saida, border=1)
                pdf.cell(col_widths[4], 10, txt=horas, border=1)
                pdf.cell(col_widths[5], 10, txt=valor, border=1)
                pdf.ln()
            
            # Totais
            pdf.ln(5)
            total_veiculos = len(relatorio)
            total_valor = sum(float(row[5]) for row in relatorio if row[5])
            pdf.cell(0, 10, txt=f"Total de Veículos: {total_veiculos}", ln=1)
            pdf.cell(0, 10, txt=f"Faturamento Total: R$ {total_valor:.2f}", ln=1)
            
            # Salvar arquivo
            nome_arquivo = f"relatorio_{titulo[:30]}.pdf".replace(" ", "_").replace("/", "-")
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", nome_arquivo)
            pdf.output(file_path)
            
            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar PDF:\n{str(e)}")

    def exportar_relatorio_excel(self, relatorio, titulo):
        """Exporta um relatório específico para Excel"""
        try:
            # Criar DataFrame
            df = pd.DataFrame(relatorio, columns=["Placa", "Tipo", "Entrada", "Saída", "Horas", "Valor"])
            
            # Formatar colunas de data/hora
            df['Entrada'] = pd.to_datetime(df['Entrada']).dt.strftime('%d/%m/%Y %H:%M')
            df['Saída'] = pd.to_datetime(df['Saída']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Calcular totais
            total_veiculos = len(df)
            total_valor = df['Valor'].sum()
            
            # Criar nome do arquivo
            nome_arquivo = f"relatorio_{titulo[:30]}.xlsx".replace(" ", "_").replace("/", "-")
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", nome_arquivo)
            
            # Criar arquivo Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Movimentações', index=False)
                
                # Adicionar resumo
                resumo = pd.DataFrame({
                    'Métrica': ['Período', 'Total Veículos', 'Faturamento Total'],
                    'Valor': [
                        titulo.split("-")[-1].strip(),
                        total_veiculos,
                        f"R$ {total_valor:.2f}"
                    ]
                })
                resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            messagebox.showinfo("Sucesso", f"Relatório exportado para:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar Excel:\n{str(e)}")

def verificar_e_atualizar_banco():
    """Verifica e atualiza a estrutura do banco se necessário"""
    conn = sqlite3.connect("estacionamento.db")
    cursor = conn.cursor()
    
    # Verifica se a coluna 'tipo' existe na tabela 'veiculos'
    cursor.execute("PRAGMA table_info(veiculos)")
    colunas = [info[1] for info in cursor.fetchall()]
    
    if 'tipo' not in colunas:
        try:
            cursor.execute("ALTER TABLE veiculos ADD COLUMN tipo TEXT DEFAULT 'Carro'")
            conn.commit()
            print("[Banco de Dados] Coluna 'tipo' adicionada com sucesso.")
        except Exception as e:
            print(f"[Erro] Falha ao atualizar o banco: {e}")
    
    conn.close()

if __name__ == "__main__":
    # Primeiro cria o banco (se não existir)
    criar_banco_dados()
    
    # Depois verifica/atualiza a estrutura
    verificar_e_atualizar_banco()
    
    # Finalmente inicia a aplicação
    app = EstacionamentoApp(ttk.Window())
    app.root.mainloop()