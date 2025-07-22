# FinanceiroMax - Sistema Financeiro Avançado

## Overview

FinanceiroMax é um sistema completo de gestão financeira desenvolvido em Python Flask, oferecendo funcionalidades avançadas como gestão de clientes, contas a pagar/receber, vendas parceladas com confirmação digital, integração WhatsApp, lembretes automáticos e sistema multi-usuário com planos de assinatura.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: HTML5 com Bootstrap 5 para interface responsiva
- **JavaScript**: Vanilla JavaScript com funcionalidades PWA
- **Progressive Web App (PWA)**: Configurado com service worker para funcionalidade offline
- **Charts**: Chart.js para visualizações de dados
- **Templates**: Sistema de templates Jinja2 do Flask

### Backend Architecture
- **Framework**: Python Flask com estrutura modular usando Blueprints
- **ORM**: SQLAlchemy com DeclarativeBase para gerenciamento de banco de dados
- **Authentication**: Sistema de sessões Flask com decoradores para controle de acesso
- **API Structure**: RESTful APIs organizadas em blueprints por funcionalidade

### Database Architecture
- **Primary**: SQLite para desenvolvimento (preparado para PostgreSQL em produção)
- **ORM**: SQLAlchemy com migrações automáticas
- **Schema**: Multi-tenant com isolamento de dados por usuário

## Key Components

### Authentication & Authorization
- **Multi-user system**: Suporte completo a múltiplos usuários
- **Role-based access**: Sistema de permissões com usuários admin e regulares
- **Session management**: Controle de sessões Flask com logout automático
- **Profile management**: Sistema completo de edição de perfil com upload de fotos

### Financial Management
- **Receivables**: Gestão de contas a receber com status e vencimentos
- **Payables**: Gestão de contas a pagar com fornecedores
- **Installment Sales**: Sistema de vendas parceladas com confirmação digital pública
- **Dashboard**: Estatísticas em tempo real com gráficos e métricas

### Client Management
- **CRUD Operations**: Gestão completa de clientes
- **Document Validation**: Validação de CPF/CNPJ brasileiros
- **Contact Management**: Integração com WhatsApp para comunicação

### WhatsApp Integration
- **Evolution API**: Integração com Evolution API para envio de mensagens
- **Instance Management**: Gerenciamento de múltiplas instâncias WhatsApp
- **Automated Reminders**: Sistema de lembretes automáticos personalizáveis

### Subscription System
- **User Plans**: Sistema de planos com limites por funcionalidade
- **Plan Types**: Free (gratuito limitado) e Premium (pago ilimitado)
- **Automatic Limits**: Verificação de limites integrada em todas as operações CRUD
- **Plan Upgrades**: Interface de self-service para upgrade de planos
- **Admin Panel**: Painel administrativo para gestão de usuários e planos

## Data Flow

### User Authentication Flow
1. Login através de formulário com validação
2. Criação de sessão Flask com dados do usuário
3. Middleware de autenticação verifica permissões em cada requisição
4. Isolamento de dados por user_id em todas as consultas

### Financial Operations Flow
1. Usuário cria transações (receivables/payables) através de formulários
2. Validação de limites de plano antes da criação
3. Armazenamento no banco com associação ao usuário
4. Atualização automática do dashboard com novas métricas

### WhatsApp Integration Flow
1. Configuração de instâncias através do Evolution API
2. Envio de mensagens via API externa
3. Logging de mensagens no banco de dados
4. Sistema de lembretes automáticos baseado em schedulers

### Installment Sales Flow
1. Criação de venda parcelada com token único
2. Geração de link público para confirmação
3. Cliente acessa link e confirma venda digitalmente
4. Criação automática de parcelas como receivables

## External Dependencies

### Core Dependencies
- **Flask**: Framework web principal
- **SQLAlchemy**: ORM para banco de dados
- **Werkzeug**: Utilitários web e segurança
- **Bootstrap 5**: Framework CSS responsivo
- **Chart.js**: Biblioteca de gráficos

### External APIs
- **Evolution API**: Integração WhatsApp (configurável via variáveis de ambiente)
- **CEP APIs**: Potencial integração para autocompletar endereços

### Environment Variables
- `DATABASE_URL`: String de conexão do banco (padrão: SQLite local)
- `SESSION_SECRET`: Chave secreta para sessões Flask
- `EVOLUTION_API_URL`: URL da API do WhatsApp
- `EVOLUTION_API_KEY`: Chave de autenticação da Evolution API

## Deployment Strategy

### Development Environment
- **Local Development**: Flask development server com debug ativado
- **Database**: SQLite local para desenvolvimento rápido
- **Hot Reload**: Configurado para recarregamento automático de código

### Production Considerations
- **Database Migration**: Preparado para migração para PostgreSQL
- **WSGI Server**: Configurado com ProxyFix para deployment atrás de proxy
- **Environment Configuration**: Todas as configurações via variáveis de ambiente
- **Session Security**: Configuração de chaves secretas para produção

### PWA Deployment
- **Service Worker**: Implementado para funcionalidade offline
- **Manifest**: Configurado para instalação como app nativo
- **Caching Strategy**: Cache de assets estáticos e dados dinâmicos

### Scalability Features
- **Modular Architecture**: Blueprints permitem fácil expansão de funcionalidades
- **Database Optimization**: Queries otimizadas com relacionamentos SQLAlchemy
- **Session Management**: Sistema de sessões escalável
- **Multi-tenancy**: Preparado para isolamento completo de dados por usuário

## Recent Changes

### Janeiro 2025
- **Sistema de IA Financeira Implementado**: Integração completa com OpenAI para análises preditivas
  - Configuração via painel administrativo (não variáveis de ambiente)
  - Predições de fluxo de caixa até 12 meses
  - Análise de risco de inadimplência de clientes
  - Insights estratégicos para otimização do negócio
  - Interface dedicada em `/ai_insights/` no menu principal

- **Sistema de Perfil de Usuário Implementado**: Gestão completa de perfil pessoal
  - Edição de nome de usuário, email e telefone
  - Alteração de senha com validação segura
  - Upload e gestão de foto de perfil com redimensionamento automático
  - Remoção de fotos antigas automaticamente
  - Estatísticas da conta na página de perfil
  - Interface acessível via menu dropdown do usuário

- **Sistema de Planos Gratuito e Premium Implementado**: Monetização com limites flexíveis
  - **Plano Gratuito**: 5 clientes, 20 contas a receber, 20 contas a pagar
  - **Plano Premium**: Recursos ilimitados por R$ 29,90/mês
  - Verificação automática de limites em todas as operações
  - Interface de upgrade integrada ao sistema
  - Notificações de limite atingido com chamadas para ação
  - Expiração automática do plano Premium (reverte para Gratuito)

The system is designed as a comprehensive financial management solution with modern web technologies, PWA capabilities, AI-powered financial insights, and extensive integration possibilities, particularly focused on the Brazilian market with CPF/CNPJ validation and WhatsApp integration.