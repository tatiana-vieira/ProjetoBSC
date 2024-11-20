class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Planejamento Estratégico', 0, 1, 'C')

    def tabela_objetivos(self, objetivos):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Objetivos', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for obj in objetivos:
            self.cell(0, 10, obj, 1, 1, 'L')

    def tabela_metas(self, metas):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Metas', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for meta in metas:
            self.cell(90, 10, meta['nome'], 1)
            self.cell(30, 10, meta['status'], 1)
            self.cell(40, 10, meta['tempo_restante'], 1, 1)

    def tabela_indicadores(self, indicadores):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Indicadores', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for indicador in indicadores:
            self.cell(60, 10, indicador['nome'], 1)
            self.cell(30, 10, str(indicador['peso']), 1)
            self.cell(40, 10, indicador['frequencia'], 1, 1)

    def tabela_acoes(self, acoes):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Ações', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        for acao in acoes:
            self.cell(90, 10, acao['nome'], 1)
            self.cell(30, 10, str(acao['execucao']), 1)
            self.cell(30, 10, acao['status'], 1)
            self.cell(40, 10, acao['tempo_restante'], 1, 1)


