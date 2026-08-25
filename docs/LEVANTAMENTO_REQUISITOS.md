## Requisitos Funcionais

| ID | Requisito |
| --- | --- |
| RF01 | O sistema deve permitir que o usuário interaja com o assistente financeiro por meio do Telegram. |
| RF02 | O sistema deve interpretar mensagens enviadas pelo usuário em linguagem natural relacionadas a despesas pessoais. |
| RF03 | O sistema deve identificar o valor monetário de uma despesa informada pelo usuário. |
| RF04 | O sistema deve identificar uma descrição objetiva para a despesa informada pelo usuário. |
| RF05 | O sistema deve classificar a despesa em uma categoria financeira predefinida. |
| RF06 | O sistema deve permitir o registro opcional da forma de pagamento utilizada na despesa. |
| RF07 | O sistema deve identificar e registrar a data da despesa quando ela for informada pelo usuário. |
| RF08 | O sistema deve utilizar a data atual quando o usuário não informar uma data para a despesa. |
| RF09 | O sistema deve solicitar esclarecimento ao usuário quando não for possível determinar de forma inequívoca o valor da despesa. |
| RF10 | O sistema deve registrar a despesa após a identificação dos dados necessários. |
| RF11 | O sistema deve armazenar a mensagem original utilizada para o registro da despesa. |
| RF12 | O sistema deve associar cada despesa ao respectivo usuário. |
| RF13 | O sistema deve confirmar ao usuário o registro realizado. |
| RF14 | O sistema deve permitir a consulta das despesas registradas em um período determinado. |
| RF15 | O sistema deve permitir a consulta das despesas de um período específico por categoria. |
| RF16 | O sistema deve informar o valor total das despesas encontradas em uma consulta. |
| RF17 | O sistema deve informar a quantidade de despesas encontradas em uma consulta. |
| RF18 | O sistema deve apresentar as despesas consultadas com suas respectivas informações relevantes, incluindo valor, descrição, categoria, forma de pagamento e data. |
| RF19 | O sistema deve permitir a consulta do total de despesas agrupadas por categoria em determinado período. |
| RF20 | O sistema deve apresentar a participação percentual de cada categoria no total das despesas do período consultado. |
| RF21 | O sistema deve ordenar as categorias de despesas de acordo com o maior valor gasto no período consultado. | Baixa |
| RF22 | O sistema deve interpretar períodos informados em linguagem natural e convertê-los em intervalos de datas para realização das consultas. |
| RF23 | O sistema deve responder às consultas financeiras utilizando os dados registrados no sistema. |
| RF24 | O sistema deve impedir que informações sobre despesas sejam inventadas ou estimadas quando não estiverem disponíveis nos registros do sistema. |
| RF25 | O sistema deve informar ao usuário quando ocorrer uma falha durante uma operação de registro ou consulta de despesas. |
| RF26 | O sistema deve direcionar mensagens que não estejam relacionadas ao propósito financeiro do assistente para o escopo de utilização do sistema. |

Esses requisitos representam principalmente o escopo funcional já implementado. Por exemplo, o sistema possui atualmente três operações centrais: `registrar_despesa`, `listar_despesas` e `resumo_por_categoria`. 

### Requisitos funcionais previstos para a evolução do projeto

O próprio README estabelece duas extensões funcionais importantes: relatórios completos com comparação entre períodos/evolução das despesas e uma camada de recomendações baseada nos dados consolidados. 

Se o documento de requisitos representar o sistema completo que você pretende entregar no projeto, eu incluiria também:

| ID | Requisito |
| --- | --- |
| RF27 | O sistema deve permitir a geração de relatórios financeiros para períodos definidos pelo usuário. |
| RF28 | O sistema deve permitir a comparação das despesas entre dois ou mais períodos selecionados pelo usuário. |
| RF29 | O sistema deve apresentar a evolução das despesas entre períodos comparáveis. |
| RF30 | O sistema deve identificar variações relevantes nos gastos entre períodos. |
| RF31 | O sistema deve consolidar os dados financeiros do usuário para utilização na geração de recomendações. |
| RF32 | O sistema deve gerar recomendações financeiras personalizadas com base nos padrões de despesas identificados nos dados do usuário. |
| RF33 | O sistema deve utilizar um modelo de linguagem adequado para processar os dados consolidados e gerar recomendações financeiras. |
| RF34 | O sistema deve apresentar as recomendações financeiras ao usuário por meio do canal conversacional. |

Esses últimos requisitos ainda não devem ser apresentados como funcionalidades implementadas, porque a documentação atual os classifica como próximos passos. 

------------------------

## Requisitos Não Funcionais

### Desempenho

| ID | Requisito | 
| --- | --- |
| RNF01 | O sistema deve processar as mensagens recebidas pelo canal de comunicação sem exigir intervenção manual para cada solicitação. |
| RNF02 | O sistema deve reutilizar conexões com o banco de dados por meio de um mecanismo de pool de conexões, evitando a abertura desnecessária de novas conexões a cada operação. |
| RNF03 | O sistema deve utilizar índices para otimizar consultas de despesas por usuário, data e categoria. |
| RNF04 | O sistema deve limitar o número de iterações consecutivas realizadas pelo agente durante o processamento de uma solicitação, evitando ciclos excessivos de chamadas de ferramentas. |
| RNF05 | O sistema deve evitar processamento redundante de uma mesma operação de registro dentro de uma única interação. |

O RNF05 é particularmente pertinente porque o próprio comportamento do agente determina que `registrar_despesa` seja chamado uma única vez e que o turno seja encerrado após o registro.

### Segurança

| ID | Requisito |
| --- | --- |
| RNF06 | O sistema deve manter credenciais de acesso e chaves de API fora do código-fonte da aplicação. |
| RNF07 | O sistema deve obter credenciais e configurações sensíveis por meio de variáveis de ambiente ou mecanismo equivalente de configuração segura. |
| RNF08 | O sistema deve impedir que credenciais armazenadas no arquivo `.env` sejam incluídas no controle de versão. |
| RNF09 | O sistema deve garantir que um usuário somente consulte informações financeiras associadas ao seu próprio cadastro. |
| RNF10 | O sistema deve associar as operações financeiras ao identificador do usuário proveniente do canal de comunicação. |
| RNF11 | O sistema não deve expor ao usuário final informações internas de configuração, credenciais, estrutura do banco ou detalhes de implementação. |
| RNF12 | O sistema deve preservar a confidencialidade dos dados financeiros armazenados durante sua utilização e transmissão. |

Aqui há uma questão importante: o RNF09 representa uma exigência de segurança necessária ao domínio, mas a implementação atual ainda possui uma fragilidade relacionada a isso. O próprio README registra como próximo passo "vincular automaticamente as despesas ao usuário do Telegram autenticado", pois atualmente o `telegram_id` é passado pelo modelo ao chamar a ferramenta. 

Portanto, eu manteria esse requisito, mas marcaria no projeto como **pendência de implementação**, e não como algo já plenamente atendido.

### Confiabilidade e integridade

| ID | Requisito |
| --- | --- |
| RNF13 | O sistema deve garantir a consistência das operações de persistência por meio de mecanismos transacionais. |
| RNF14 | O sistema deve desfazer alterações pendentes no banco de dados quando ocorrer uma falha durante uma operação transacional. |
| RNF15 | O sistema deve impedir o armazenamento de despesas com valores menores ou iguais a zero. |
| RNF16 | O sistema deve garantir a integridade referencial entre usuários, categorias e despesas. |
| RNF17 | O sistema deve manter os dados persistidos após a reinicialização dos serviços da aplicação. |
| RNF18 | O sistema deve tratar falhas das ferramentas sem produzir respostas financeiras baseadas em informações inexistentes ou estimadas. |
| RNF19 | O sistema deve preservar a mensagem original associada a uma despesa para possibilitar rastreabilidade da operação. |

A implementação já possui `CHECK (valor > 0)`, chaves estrangeiras e transações com `commit` e `rollback`.  

### Disponibilidade

| ID | Requisito |
| --- | --- |
| RNF20 | O sistema deve iniciar automaticamente os serviços necessários para sua operação quando executado por meio do ambiente Docker Compose configurado. |
| RNF21 | O sistema deve verificar a disponibilidade do banco de dados antes de iniciar o serviço dependente dele. |
| RNF22 | O sistema deve permitir a reinicialização dos serviços sem necessidade de reconstrução manual do ambiente. |
| RNF23 | O sistema deve disponibilizar mecanismos para identificar se o agente está em execução e conectado aos serviços necessários. |

Isso não é apenas uma suposição: o `docker-compose.yml` possui `healthcheck` para o PostgreSQL e `depends_on` condicionado ao estado saudável do banco. 

### Usabilidade

| ID | Requisito |
| --- | --- |
| RNF24 | O sistema deve permitir que o usuário interaja com suas funcionalidades utilizando linguagem natural. |
| RNF25 | O sistema deve apresentar respostas em português do Brasil. |
| RNF26 | O sistema deve apresentar respostas em linguagem natural, evitando a exposição direta das estruturas retornadas pelas ferramentas internas. |
| RNF27 | O sistema deve apresentar confirmações de registro de forma objetiva e compreensível. |
| RNF28 | O sistema deve solicitar informações adicionais quando os dados fornecidos pelo usuário forem insuficientes para executar uma operação com segurança. |
| RNF29 | O sistema deve informar ao usuário quando uma operação não puder ser realizada devido a uma falha interna. |

O próprio `SOUL.md` determina respostas naturais e curtas para confirmações, além de exigir esclarecimento quando o valor da despesa for ambíguo. 

### Manutenibilidade

| ID | Requisito |
| --- | --- |
| RNF30 | O sistema deve manter separadas as responsabilidades de comunicação, processamento do agente, acesso aos dados e persistência. |
| RNF31 | O sistema deve permitir a evolução das ferramentas financeiras sem necessidade de modificar diretamente a camada de comunicação com o usuário. |
| RNF32 | O sistema deve permitir a alteração do modelo de linguagem utilizado por meio de configuração. |
| RNF33 | O sistema deve manter as configurações do agente separadas de sua implementação. |
| RNF34 | O sistema deve possuir documentação suficiente para instalação, configuração, execução e diagnóstico da aplicação. |
| RNF35 | O sistema deve permitir a configuração do limite de iterações do agente sem alteração do código-fonte. |
| RNF36 | O sistema deve utilizar dependências declaradas de forma que o ambiente possa ser reproduzido. |

O modelo, por exemplo, é definido por `GEMINI_MODEL`, enquanto o limite de iterações está configurado no arquivo do agente. 

### Portabilidade

| ID | Requisito |
| --- | --- |
| RNF37 | O sistema deve ser executável em ambiente conteinerizado utilizando Docker. |
| RNF38 | O sistema deve permitir a execução do ambiente completo por meio do Docker Compose. |
| RNF39 | O sistema deve possuir configuração específica para execução local e configuração específica para execução em containers. |
| RNF40 | O sistema deve manter suas dependências de execução declaradas em arquivos de configuração do projeto. |
| RNF41 | O sistema deve permitir a reconstrução do ambiente de execução sem depender de configurações manuais previamente realizadas na máquina hospedeira. |

O projeto possui Dockerfiles separados, `docker-compose.yml`, `requirements.txt` e configurações distintas do Nanobot para execução local e Docker. 

### Interoperabilidade

| ID | Requisito |
| --- | --- |
| RNF42 | O sistema deve ser capaz de integrar-se ao Telegram para recebimento e envio de mensagens. |
| RNF43 | O sistema deve permitir a integração do agente com ferramentas externas por meio do protocolo MCP. |
| RNF44 | O sistema deve utilizar uma API de modelo de linguagem para processamento das interações conversacionais. |
| RNF45 | O sistema deve permitir a comunicação entre o agente e o servidor de ferramentas sem acoplamento direto entre a lógica conversacional e a lógica de persistência. |

A arquitetura atual efetivamente separa o agente das ferramentas MCP, que fornecem as operações de registro e consulta. 

### Observabilidade e diagnóstico

| ID | Requisito |
| --- | --- |
| RNF46 | O sistema deve disponibilizar logs para acompanhamento da execução do agente. |
| RNF47 | O sistema deve permitir a identificação de falhas de conexão com o servidor MCP. |
| RNF48 | O sistema deve permitir a identificação de falhas relacionadas à API do modelo de linguagem. |
| RNF49 | O sistema deve disponibilizar informações suficientes para diagnosticar falhas de inicialização dos serviços. |
| RNF50 | O sistema deve permitir o acompanhamento do estado dos containers que compõem a aplicação. |

O README já documenta explicitamente o uso de logs do Nanobot, verificação do estado dos containers e identificação da conexão do MCP. 

### Configurabilidade

| ID | Requisito |
| --- | --- |
| RNF51 | O sistema deve permitir a configuração das credenciais do Telegram sem alteração do código-fonte. |
| RNF52 | O sistema deve permitir a configuração das credenciais da API do modelo de linguagem sem alteração do código-fonte. |
| RNF53 | O sistema deve permitir a configuração do modelo de linguagem utilizado sem alteração da lógica de negócio. |
| RNF54 | O sistema deve permitir a configuração da conexão com o banco de dados por meio de configuração externa. |
| RNF55 | O sistema deve permitir a configuração do ambiente de execução sem necessidade de modificar os arquivos responsáveis pela lógica das operações financeiras. |

Isso é coerente com a utilização de `TELEGRAM_TOKEN`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `DATABASE_URL` e `POSTGRES_PASSWORD` como configurações externas. 

### Rastreabilidade

| ID | Requisito |
| --- | --- |
| RNF56 | O sistema deve manter a data e hora de criação dos registros de usuário e despesa. |
| RNF57 | O sistema deve manter a mensagem original utilizada como origem do registro de uma despesa. |
| RNF58 | O sistema deve permitir identificar o usuário responsável por cada despesa armazenada. |
| RNF59 | O sistema deve manter identificadores únicos para usuários, categorias e despesas. |

O schema já possui identificadores próprios e `criado_em` para usuários e despesas, além de `mensagem_original`. 
