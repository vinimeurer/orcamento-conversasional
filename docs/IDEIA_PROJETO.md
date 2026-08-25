# Orçamento Conversacional: Uma Abordagem Leve para Gestão Financeira Pessoal com LLMs Locais para Jovens Adultos

## Resumo do Projeto

O projeto propõe o desenvolvimento e a avaliação de um protótipo de gestão financeira pessoal baseado em interação conversacional com Inteligência Artificial, tendo como público-alvo jovens adultos entre 18 e 29 anos.

A ideia principal é permitir que o usuário registre seus gastos utilizando linguagem natural, sem a necessidade de preencher formulários ou utilizar planilhas manualmente. Por exemplo:

> "Gastei R$ 35 no almoço hoje."

A partir dessa mensagem, o sistema deverá identificar as principais informações da transação, como valor, descrição e categoria, e realizar o registro automaticamente.

Além do registro de despesas, o sistema deverá permitir que o usuário consulte seus dados financeiros por meio de períodos personalizados, gere relatórios e obtenha recomendações a partir dos resultados encontrados.

O projeto busca investigar se uma interface conversacional pode reduzir a dificuldade e o esforço envolvidos no registro e acompanhamento das despesas, mantendo um nível aceitável de confiabilidade.

## Objetivo

O objetivo principal é investigar a viabilidade do uso de modelos de linguagem compactos executados localmente como interface conversacional para gestão financeira pessoal de jovens adultos.

O sistema deverá permitir:

- Registrar despesas por meio de linguagem natural;
- Consultar informações financeiras utilizando perguntas em linguagem natural;
- Gerar relatórios para períodos definidos pelo usuário;
- Analisar os registros financeiros armazenados;
- Identificar padrões e categorias de maior impacto nos gastos;
- Gerar recomendações personalizadas a partir dos resultados encontrados.

O projeto não pretende desenvolver um aplicativo financeiro completo ou realizar uma comparação abrangente entre diferentes modelos de linguagem. O foco está em avaliar, por meio de um protótipo funcional, se uma abordagem conversacional baseada em IA local pode ser uma alternativa viável ao registro e acompanhamento financeiro tradicional.

## Público-Alvo

O público-alvo definido para a avaliação do protótipo são **jovens adultos entre 18 e 29 anos**.

A escolha dessa faixa etária está relacionada ao caráter exploratório do projeto. Esse público apresenta, em comparação com outras faixas etárias, maior familiaridade com tecnologias digitais e ferramentas de inteligência artificial. Segundo o Pew Research Center, 66% dos adultos entre 18 e 29 anos já utilizaram chatbots de inteligência artificial, indicando uma elevada familiaridade desse grupo com esse tipo de tecnologia (GOTTFRIED et al., 2026). Esse contexto torna o grupo adequado para uma investigação inicial sobre uma interface financeira baseada em conversação.

A seleção do público não tem como objetivo afirmar que a solução seja aplicável exclusivamente a jovens adultos. O recorte busca estabelecer um grupo inicial de usuários com maior familiaridade tecnológica, permitindo avaliar principalmente a viabilidade técnica e prática da proposta antes de possíveis estudos futuros com públicos mais amplos e heterogêneos.

## Motivação

O controle financeiro pessoal normalmente depende de aplicativos estruturados, planilhas ou formulários. Embora essas ferramentas sejam eficientes, elas exigem que o usuário interrompa sua atividade para preencher informações de maneira estruturada, o que pode tornar o acompanhamento das despesas uma tarefa pouco prática no cotidiano.

Para jovens adultos, o acompanhamento das próprias finanças pode ser especialmente relevante, uma vez que essa fase está frequentemente associada à transição entre a dependência financeira e a independência. Estudos sobre independência financeira de jovens adultos destacam essa transição e apontam a importância de habilidades relacionadas à administração do dinheiro nesse período (XIAO; CHATTERJEE; KIM, 2014). Dados do Pew Research Center também indicam que essa independência ocorre de forma gradual: entre jovens de 18 a 24 anos, apenas 16% afirmam ser completamente independentes financeiramente dos pais, enquanto entre aqueles de 25 a 29 anos esse percentual chega a 44% (MINKIN et al., 2024).

Nesse contexto, a necessidade de realizar registros financeiros manualmente pode representar uma barreira para a utilização contínua de ferramentas de controle financeiro. A proposta do projeto é explorar uma alternativa baseada em linguagem natural, permitindo que o registro financeiro se aproxime de uma conversa cotidiana. Dessa forma, o usuário poderia registrar uma despesa simplesmente informando o que aconteceu, sem a necessidade de preencher campos estruturados.

Além do registro, a solução busca facilitar também a etapa de acompanhamento e análise das finanças. O usuário poderá solicitar informações sobre seus gastos utilizando períodos personalizados, permitindo que o sistema gere relatórios e apresente os principais resultados de maneira compreensível.

Com base nessas informações, o sistema também poderá apresentar recomendações, como identificar categorias que concentram uma parcela elevada dos gastos ou indicar possíveis pontos de atenção no comportamento financeiro. Dessa maneira, o projeto busca investigar se uma interface conversacional baseada em inteligência artificial pode tornar o acompanhamento das finanças pessoais mais simples e acessível para jovens adultos.

## Arquitetura da Solução

A arquitetura será dividida em diferentes responsabilidades, buscando utilizar cada modelo de linguagem de acordo com a complexidade da tarefa.

O **Nanobot** será utilizado como estrutura de gerenciamento do agente e integração com a interface conversacional do Telegram.

De forma simplificada:

**Usuário → Telegram → Nanobot → LLM → Registro/Consulta**

e, quando necessário:

**Dados financeiros → LLM → Análise → Recomendação**

Essa abordagem busca equilibrar **custo, desempenho e capacidade de análise**.

Os dados utilizados para gerar uma recomendação poderão ser previamente consolidados pelo sistema antes do envio à API, evitando o envio desnecessário de todo o histórico financeiro do usuário.

## Tecnologias

O protótipo utilizará principalmente:

- **Telegram**, como interface de interação;
- **Nanobot**, para gerenciamento e orquestração do agente;
- **LLM**, para as tarefas conversacionais e de interpretação;
- **LLM**, para análises e recomendações mais complexas;
- Banco de dados para armazenamento das informações financeiras.

Documentação do Nanobot:

https://github.com/HKUDS/nanobot/tree/main/docs

## Funcionalidades

### 1. Registro financeiro

O usuário poderá registrar despesas utilizando linguagem natural.

Exemplo:

> "Paguei R$ 120 no mercado hoje no cartão."

O sistema deverá identificar as informações relevantes e armazenar o registro de forma estruturada.

### 2. Consultas financeiras

O usuário poderá realizar perguntas utilizando linguagem natural.

Exemplos:

> "Quanto gastei em alimentação este mês?"

> "Quanto gastei entre 1º e 15 de agosto?"

> "Quanto gastei com transporte no último trimestre?"

### 3. Relatórios

A partir dos registros armazenados, o sistema poderá gerar relatórios para períodos personalizados.

Os relatórios poderão apresentar:

- Total de gastos;
- Distribuição por categoria;
- Gastos por período;
- Comparação entre períodos;
- Categorias com maior participação;
- Evolução das despesas.

### 4. Recomendações

A partir dos resultados consolidados, o sistema poderá encaminhar as informações relevantes para uma **LLM por meio de uma API**, responsável por realizar uma análise mais elaborada e gerar recomendações.

A utilização de uma LLM mais avançada nessa etapa ocorre porque a geração de recomendações exige uma capacidade de interpretação e raciocínio superior à necessária para tarefas simples de registro e classificação.

Por exemplo, após analisar os dados de determinado período, o sistema poderia identificar:

> "Seus gastos com alimentação aumentaram 28% em relação ao período anterior."

A LLM poderia então utilizar essa informação, juntamente com outros dados relevantes, para produzir uma recomendação contextualizada.

As recomendações terão caráter **informativo e educacional**, não constituindo aconselhamento financeiro profissional.

## Estratégia de Uso das LLMs

Um dos aspectos investigados pelo projeto será justamente a utilização de modelos diferentes de acordo com a complexidade da tarefa.

As tarefas simples e frequentes serão executadas localmente, enquanto tarefas mais complexas serão encaminhadas para uma LLM mais avançada.

| Tipo de tarefa | Modelo |
|---|---|
| Registro de despesas | Qwen 2.5 3B local |
| Identificação de informações | Qwen 2.5 3B local |
| Consultas simples | Qwen 2.5 3B local |
| Organização dos dados | Sistema determinístico |
| Geração de relatórios | Sistema + LLM local |
| Análise financeira mais complexa | LLM avançada via API |
| Recomendações | LLM avançada via API |

Essa arquitetura permite explorar uma abordagem híbrida, na qual a IA local é priorizada sempre que possível, enquanto recursos externos são utilizados somente quando agregam valor à tarefa.

## Avaliação

Após a implementação do protótipo, será realizada uma avaliação exploratória com um pequeno grupo de jovens adultos entre 18 e 29 anos.

Serão observados aspectos como:

- Tempo necessário para registrar uma despesa;
- Quantidade de correções necessárias;
- Tipos de erros cometidos pelo sistema;
- Necessidade de confirmações adicionais;
- Facilidade de utilização;
- Percepção de esforço;
- Naturalidade da interação;
- Facilidade para consultar informações;
- Utilidade percebida dos relatórios;
- Utilidade percebida das recomendações.

A avaliação terá caráter exploratório e descritivo, com o objetivo de identificar padrões de comportamento, dificuldades e limitações da proposta.

## Pergunta de Pesquisa

---

> a definir

---

## Hipótese

A hipótese do projeto é que uma interface conversacional baseada em um modelo de linguagem pode proporcionar uma experiência de gestão financeira com menor fricção percebida do que métodos estruturados tradicionais, mantendo uma frequência de erros e correções operacionalmente aceitável.

Além disso, espera-se que a possibilidade de realizar consultas, gerar relatórios e receber recomendações por meio de linguagem natural torne o acompanhamento financeiro mais acessível e frequente.

## Resultados Esperados

Espera-se verificar se o uso de uma interface conversacional pode tornar o registro e o acompanhamento das despesas mais simples, rápido e natural para jovens adultos.

O projeto também deverá avaliar se a utilização de linguagem natural facilita não apenas o registro, mas também a consulta e interpretação das informações financeiras.

Espera-se que o sistema seja capaz de:

- Registrar despesas de maneira conversacional;
- Recuperar informações de períodos personalizados;
- Gerar relatórios financeiros básicos;
- Identificar padrões de gastos;
- Apresentar categorias de maior impacto;
- Gerar recomendações contextualizadas utilizando uma LLM mais avançada.

Além disso, o projeto deverá permitir identificar as principais limitações do uso de modelos de linguagem compactos em uma aplicação prática, especialmente em situações envolvendo linguagem informal, abreviações, ambiguidades e diferentes formas de descrever uma mesma transação.

O resultado esperado não é comprovar que a solução é superior aos métodos tradicionais em todos os aspectos, mas determinar se existe **viabilidade técnica e prática suficiente para justificar o desenvolvimento de soluções semelhantes em trabalhos futuros**.

## Conceito de Orçamento Conversacional

O conceito central do projeto é o **Orçamento Conversacional**: utilizar a linguagem natural como principal forma de interação com uma ferramenta de gestão financeira pessoal.

Em vez de adaptar o comportamento do usuário à estrutura de um sistema, busca-se permitir que o usuário se comunique de maneira natural e que o sistema transforme essa comunicação em informações financeiras estruturadas.

Dessa forma, o projeto investiga não apenas a capacidade da IA de interpretar corretamente uma despesa, mas também sua capacidade de auxiliar o usuário na **consulta, compreensão e acompanhamento de sua situação financeira**.

O fluxo geral da proposta pode ser representado como:

**Conversa → Registro → Organização → Consulta → Relatório → Análise → Recomendação**

## Relevância do Projeto

O projeto está situado na interseção entre **Inteligência Artificial, Engenharia de Software e Interação Humano-Computador**, explorando o uso de modelos de linguagem compactos em uma aplicação prática de interesse cotidiano.

A utilização de modelos locais permite investigar uma alternativa que combina **privacidade, baixo custo e independência de serviços externos**, enquanto a utilização pontual de uma LLM mais avançada permite ampliar a capacidade analítica do sistema sem tornar toda a solução dependente de uma API externa.

A partir da avaliação com jovens adultos, o trabalho poderá fornecer uma primeira evidência sobre a viabilidade da utilização de LLMs locais como interface para gestão financeira pessoal, servindo como base para futuras pesquisas e evoluções da solução.

## Referências

GOTTFRIED, Jeffrey; BISHOP, William; ANDERSON, Monica; FAVERIO, Michelle; PARK, Eunice; MCCLAIN, Colleen. **How opinions and use of AI differ by age**. Pew Research Center, Washington, D.C., 17 jun. 2026. Disponível em:<https://www.pewresearch.org/internet/2026/06/17/how-opinions-and-use-of-ai-differ-by-age/>. Acesso em: 25 ago. 2026.

MINKIN, Rachel; PARKER, Kim; HOROWITZ, Juliana Menasce; ARAGÃO, Carolina. **Financial help and independence in young adulthood**. Pew Research Center, 25 jan. 2024. Disponível em:<https://www.pewresearch.org/social-trends/2024/01/25/financial-help-and-independence-in-young-adulthood/>. Acesso em: 25 ago. 2026. 

XIAO, Jing Jian; CHATTERJEE, Swarn; KIM, Jinhee. **Factors associated with financial independence of young adults**. International Journal of Consumer Studies, v. 38, n. 4, p. 394–403, 2014. DOI: 10.1111/ijcs.12106. Disponível em:<https://doi.org/10.1111/ijcs.12106>. Acesso em: 25 ago. 2026.