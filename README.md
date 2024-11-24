# Kika Campo - Sistema de Agendamento de Campo de Futebol

Este é um sistema web para gerenciamento de agendamentos de horários para um campo de futebol. O sistema permite que clientes façam reservas de horários e realizem pagamentos via PIX ou dinheiro, além de fornecer um painel administrativo para gerenciamento das reservas.

## Funcionalidades

### Para Clientes
- Cadastro de usuário com nome, e-mail, telefone e senha
- Visualização de horários disponíveis
- Agendamento de horários
- Opções de pagamento: PIX (QR Code) ou dinheiro
- Histórico de reservas
- Chat em tempo real com o administrador

### Para Administradores
- Painel administrativo protegido
- Visualização e gerenciamento de agendamentos
- Confirmação de pagamentos
- Gerenciamento de horários disponíveis
- Sistema de mensagens com clientes
- Estatísticas e relatórios
- Visualização detalhada de informações dos clientes

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/Mateus123400/CampodoKika.git
cd CampodoKika
```

2. Crie um ambiente virtual Python:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. O sistema já vem configurado com um banco de dados SQLite
2. O código de administrador padrão é: kika01

## Executando o Sistema

1. Ative o ambiente virtual (se ainda não estiver ativo)

2. Execute o aplicativo:
```bash
python app.py
```

3. Acesse o sistema no navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

```
CampodoKika/
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências do projeto
├── static/            # Arquivos estáticos
│   ├── css/
│   │   └── style.css
│   ├── img/           # Imagens do campo
│   │   ├── campo1.jpg
│   │   └── campo2.jpg
│   └── js/
│       └── main.js
└── templates/         # Templates HTML
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── admin_dashboard.html
    ├── user_details.html
    └── messages.html
```

## Segurança

- Senhas são armazenadas com hash seguro
- Autenticação necessária para todas as operações sensíveis
- Código de administrador protegido (kika01)
- Sessões seguras com Flask-Login
- Proteção contra CSRF
- Validação de entrada de dados

## Recursos Técnicos

- Flask (Framework web)
- SQLAlchemy (ORM)
- Flask-Login (Autenticação)
- Flask-SocketIO (Chat em tempo real)
- Bootstrap 5 (Frontend)
- JavaScript (Interatividade)
- SQLite (Banco de dados)

## Contribuição

Para contribuir com o projeto:

1. Faça um Fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das mudanças (`git commit -m 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Suporte

Em caso de dúvidas ou problemas, entre em contato:
- Email: marianealves23p@gmail.com
- GitHub: [@Mateus123400](https://github.com/Mateus123400)

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
