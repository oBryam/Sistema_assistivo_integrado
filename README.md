# Sistema Assistivo Integrado v0.2

Aplicação desenvolvida em **Python** como uma **Tecnologia Digital da Informação e Comunicação (TDIC)** aliada à **Tecnologia Assistiva (TA)**. O software foi estruturado para fornecer total autonomia a estudantes com baixa visão, fotofobia e dificuldades no processamento de textos extensos ou bloqueados, com **total independência entre as funcionalidades**.

---

## ⚡ Novidades da Versão 0.2 (Refinamento Visual & Estabilidade)

1. **Interface Despoluída e Ergonômica**:
   - Redução da sobrecarga cognitiva: eliminação de blocos repetitivos de texto e barras de rolagem desnecessárias.
   - Janela compacta e moderna com cartões limpos e controles objetivos.
2. **Alternância entre Modo Escuro e Modo Claro**:
   - Botão no cabeçalho `☀️ Claro` / `🌙 Escuro` com troca instantânea de paleta de cores.
   - O tema escolhido é salvo automaticamente no `config.json`.
3. **OCR Instantâneo com Seleção Visual de Área (`Ctrl + Alt + O`)**:
   - Abre uma sobreposição translúcida com mira de alta precisão.
   - O estudante clica e arrasta um retângulo amarelo diretamente sobre o texto/imagem que deseja ler.
4. **Lupa com Ancoragem, Régua Guia e Movimento Amortecido**:
   - Modo Ancorado (faixa fixa no topo ou base da tela) e Modo Flutuante com interpolação suave (*lerp*).
   - Régua horizontal amarela com foco suave para guiar a leitura linha a linha.
5. **Síntese de Voz (TTS) com Pausa/Retomada e Karaokê**:
   - Pausa e retomada (`Ctrl + Alt + Espaço`) sem perder o buffer.
   - Destaque em tempo real da sentença ativa na caixa de texto.
6. **5 Modos de Contraste Global para Fotofobia (`Ctrl + Alt + I`)**:
   - Normal, Invertido, Preto/Amarelo, Âmbar (Anti-Luz Azul) e Escala de Cinza aplicados a toda a tela do Windows.

---

## ⌨️ Tabela Completa de Atalhos Globais (v0.2)

| Recurso | Atalho Global | Função |
| :--- | :---: | :--- |
| **Lupa Virtual** | `Ctrl + Alt + L` | Liga / desliga a lente ampliada |
| **Aumentar Zoom** | `Ctrl + +` / `Mouse Wheel ▲` | Aumenta a escala (até 6.0x) |
| **Diminuir Zoom** | `Ctrl + -` / `Mouse Wheel ▼` | Reduz a escala (até 1.5x) |
| **Contraste Global (5 Modos)** | `Ctrl + Alt + I` | Alterna: *Normal ➔ Invertido ➔ Preto/Amarelo ➔ Âmbar ➔ Cinza* |
| **Ler Texto Selecionado** | `Ctrl + Alt + R` | Captura a seleção e vocaliza via TTS |
| **OCR de Imagem da Tela** | `Ctrl + Alt + O` | Captura a imagem sob o mouse, extrai texto e lê em voz alta |
| **Pausar / Retomar Leitura** | `Ctrl + Alt + Espaço` | Pausa ou continua a fala no ponto exato |
| **Parar Fala Imediatamente** | `Ctrl + Alt + P` | Cancela imediatamente a leitura em curso |

---

## 🚀 Como Executar

### 1. Versão Portátil (Sem instalar nada)
Dê um duplo clique no arquivo executável gerado:
- **[Sistema_Assistivo_Integrado_v0.2.exe](file:///c:/Users/04828103007/Desktop/TA/Sistema_Assistivo_Integrado_v0.2.exe)**

### 2. Execução via Python
```bash
pip install -r requirements.txt
python main.py
```

### 3. Testes Automatizados
```bash
python test_assistive_app.py
```
