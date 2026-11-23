# Sistema Assistivo Integrado v0.1

Aplicação desenvolvida em **Python** como uma **Tecnologia Digital da Informação e Comunicação (TDIC)** aliada à **Tecnologia Assistiva (TA)**. O software foi estruturado para fornecer total autonomia a estudantes com baixa visão, fotofobia e dificuldades na leitura de textos extensos, com **total independência entre as funcionalidades**.

---

## ⚡ Independência Total entre as Funções

Cada um dos três recursos principais funciona de forma autônoma:
1. **Lupa Dinâmica**: Pode ser ligada ou desligada a qualquer momento, sem interferir no contraste da tela ou na leitura de texto.
2. **Adaptação Cromática para Fotofobia**: Funciona **sempre, em toda a tela do sistema operacional** (Windows Magnification API), protegendo contra luz ofuscante mesmo com a lupa desativada.
3. **Leitura Auditiva (TTS)**: Funciona continuamente em segundo plano para qualquer janela ou texto selecionado, independentemente de a lupa estar aberta ou do modo de cor ativo.

---

## 🏛️ Detalhamento dos Quatro Eixos Operacionais

### 1. Painel Principal de Alto Contraste
- **Esquema Cromático Estrito**: Fundo preto profundo (`#0A0A0A` e `#161616`) com tipografia ampliada em **Amarelo vibrante (`#FFE600`)** e **Branco puro (`#FFFFFF`)**.
- **Controles Intuitivos**: Botões grandes com alto relevo e respostas visuais imediatas.
- **Confirmação Sonora**: Bipes distintos emitidos via `winsound.Beep` para inicialização, acionamento de lupa, ajuste de zoom, mudança de filtro e vocalização.

### 2. Lupa Dinâmica com Área Ampla
- **Área Significativamente Aumentada**: Para resolver o problema de campo visual restrito, a lupa agora conta com dimensões generosas:
  - **Média**: `520 x 380 px`
  - **Grande (Padrão)**: `700 x 500 px` *(quase 3x a área original)*
  - **Panorâmica**: `900 x 560 px` *(ideal para leitura contínua de parágrafos inteiros)*
- **Escala de 1.5x a 6.0x**: Ajustável a qualquer instante via `Ctrl + "+"` / `Ctrl + "-"` ou pela **roda de rolagem do mouse**.
- **Não Rouba Foco**: Opera com `WS_EX_NOACTIVATE` e `WDA_EXCLUDEFROMCAPTURE`, evitando que a lente trave a digitação do aluno ou produza espelhamento infinito.

### 3. Adaptação Cromática Global para Fotofobia
- **Atuação em Toda a Tela**: Aplica matriz de transformação de cores diretamente ao monitor via API nativa do Windows (`Magnification.dll`).
- **Três Modos Disponíveis**:
  1. **Normal**: Cores padrão do sistema operacional.
  2. **Invertido (Anti-Brilho)**: Inverte todo o espectro cromático, convertendo páginas web e PDFs brancos em fundos escuros.
  3. **Alto Contraste Preto e Amarelo**: Remove a luz azul e o brilho excessivo, mapeando o fundo para preto absoluto (`#000000`) e caracteres para amarelo vívido (`#FFE600`).
- **Atalho Global**: Alterne a qualquer momento com **`Ctrl + Alt + I`**, esteja a lupa aberta ou não.

### 4. Leitura Auditiva de Textos Extensos (TTS Resiliente)
- **Multi-Modalidade de Entrada**:
  - **Seleção na Tela (`Ctrl + Alt + R`)**: Selecione qualquer texto em PDFs, navegadores ou editores e pressione o atalho.
  - **Colar e Ler**: Botão rápido no painel para ler imediatamente o conteúdo da área de transferência.
  - **Caixa de Texto Direta**: Permite digitar ou colar textos diretamente no painel para vocalização assistida.
- **Voz Nativa em Português**: Configurado com voz brasileira (**Microsoft Maria Desktop - pt-BR**).
- **Interrupção Instantânea (`Ctrl + Alt + P`)**: Purga o buffer de fala na hora, sem travamentos.
- **Ajuste de Velocidade**: Controle deslizante no painel (-4 a +6) para adequação ao ritmo cognitivo do estudante.

---

## ⌨️ Tabela de Atalhos Globais

| Recurso | Atalho Global | Descrição |
| :--- | :---: | :--- |
| **Lupa Dinâmica** | `Ctrl + Alt + L` | Liga / desliga a lente flutuante de área ampla |
| **Aumentar Zoom** | `Ctrl + +` ou `Mouse Wheel ▲` | Aumenta a ampliação (até 6.0x) |
| **Diminuir Zoom** | `Ctrl + -` ou `Mouse Wheel ▼` | Reduz a ampliação (até 1.5x) |
| **Contraste de Tela** | `Ctrl + Alt + I` | Alterna modo cromático em toda a tela *(Normal → Invertido → Preto/Amarelo)* |
| **Vocalizar Texto** | `Ctrl + Alt + R` | Captura a seleção e vocaliza em voz alta |
| **Parar Fala** | `Ctrl + Alt + P` | Interrompe imediatamente a leitura em curso |

---

## 🚀 Como Executar

```bash
python main.py
```
*(Para executar testes automatizados: `python test_assistive_app.py`)*
