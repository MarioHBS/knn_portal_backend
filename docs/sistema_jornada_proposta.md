# Sistema de Jornada - Journey Club Portal

## Visão Geral

O Sistema de Jornada é um componente central do Journey Club Portal, implementando conceitos de gamificação para aumentar o engajamento dos alunos e funcionários com a plataforma. Este sistema transforma a experiência do usuário em uma jornada progressiva, recompensando ações, incentivando a participação contínua e oferecendo benefícios exclusivos baseados no nível de engajamento.

## Arquitetura

### Componentes Principais

1. **Módulo de Pontuação**
   - Gerencia a atribuição e cálculo de pontos de experiência (XP)
   - Registra todas as atividades pontuáveis
   - Calcula o progresso e determina o nível atual do usuário

2. **Módulo de Níveis**
   - Define a hierarquia de níveis (Bronze, Prata, Ouro, etc.)
   - Estabelece os requisitos de pontos para cada nível
   - Gerencia as transições entre níveis

3. **Módulo de Conquistas**
   - Rastreia as conquistas (achievements) disponíveis
   - Verifica condições para desbloqueio de conquistas
   - Atribui recompensas por conquistas alcançadas

4. **Módulo de Benefícios**
   - Gerencia os benefícios disponíveis por nível
   - Controla o acesso a benefícios exclusivos
   - Rastreia o uso de benefícios

5. **Módulo de Visualização**
   - Exibe o progresso da jornada nas interfaces do usuário
   - Apresenta notificações e feedback visual
   - Mostra conquistas e próximos objetivos

### Integração com Outros Sistemas

- **Sistema de Autenticação**: Identifica o usuário e seu perfil
- **Sistema de Parceiros**: Conecta benefícios de parceiros aos níveis de jornada
- **Sistema de Histórico**: Registra atividades para pontuação e conquistas
- **Sistema de Notificações**: Informa sobre novos níveis e conquistas

## Funcionalidades Atuais

### Sistema de Pontuação (XP)

Os usuários ganham pontos de experiência (XP) através de diversas atividades:

- **Cadastro e Onboarding**: Pontos iniciais por completar o cadastro
- **Login Regular**: Pontos por acessos diários (com limite diário)
- **Favoritos**: Pontos por adicionar parceiros aos favoritos
- **Visitas a Parceiros**: Pontos por visitar páginas de parceiros
- **Uso de Benefícios**: Pontos por utilizar benefícios de parceiros
- **Compartilhamento**: Pontos por compartilhar conteúdo da plataforma
- **Feedback**: Pontos por fornecer feedback sobre parceiros

### Níveis e Progressão

O sistema atual implementa uma hierarquia de níveis:

1. **Bronze** (0-1000 pontos): Nível inicial
2. **Prata** (1001-2000 pontos): Segundo nível
3. **Ouro** (2001-5000 pontos): Terceiro nível
4. **Platina** (5001-10000 pontos): Quarto nível
5. **Diamante** (10001+ pontos): Nível máximo

Cada nível oferece:
- Título visual no perfil
- Acesso a benefícios específicos
- Desbloqueio de funcionalidades exclusivas

### Conquistas (Achievements)

O sistema inclui conquistas que podem ser desbloqueadas:

- **Primeiro Login**: Completou o primeiro acesso ao portal
- **Explorador**: Visitou 10 parceiros diferentes
- **Favoritos**: Adicionou 5 parceiros aos favoritos
- **Engajado**: Usou benefícios 20 vezes
- **Fiel**: Realizou login por 7 dias consecutivos
- **Economizador**: Economizou um total de R$500 com benefícios

Cada conquista concede:
- Pontos de experiência bônus
- Emblema visual no perfil
- Notificação de desbloqueio

### Interface Visual

O sistema de jornada é apresentado visualmente em:

1. **ProfilePage**:
   - Card "Sua Jornada" com:
     - Nível atual e progresso
     - Pontos acumulados
     - Barra de progresso para próximo nível
   - Card "Conquistas" com lista de achievements

2. **DashboardPage**:
   - Seção "Sua Jornada" com barra de progresso e nível atual
   - Exibição de pontos e próximo nível

### Benefícios por Nível

Cada nível de jornada desbloqueia benefícios específicos:

- **Bronze**: Acesso básico a todos os parceiros
- **Prata**: Descontos exclusivos em parceiros selecionados
- **Ouro**: Atendimento prioritário e promoções especiais
- **Platina**: Benefícios VIP e acesso antecipado a novas promoções
- **Diamante**: Benefícios premium e descontos máximos

## Fluxos de Trabalho

### Fluxo de Pontuação

1. Usuário realiza uma ação pontuável (login, favorito, etc.)
2. Sistema registra a ação no histórico
3. Sistema calcula e atribui os pontos correspondentes
4. Sistema verifica se houve mudança de nível
5. Sistema atualiza o perfil do usuário
6. Interface exibe feedback visual (animação, notificação)

### Fluxo de Conquistas

1. Sistema monitora continuamente as ações do usuário
2. Quando condições de uma conquista são atendidas:
   - Sistema desbloqueia a conquista
   - Pontos bônus são adicionados
   - Notificação é enviada ao usuário
   - Emblema é adicionado ao perfil

### Fluxo de Benefícios

1. Usuário acessa a página de um parceiro
2. Sistema verifica o nível atual do usuário
3. Sistema exibe benefícios disponíveis para o nível
4. Usuário seleciona um benefício
5. Sistema registra o uso do benefício
6. Pontos são atribuídos pela utilização

## Implementação Técnica

### Estrutura de Dados

```typescript
// Modelo de Usuário com Jornada
interface UserJourney {
  userId: string;
  level: number;
  currentPoints: number;
  totalPointsEarned: number;
  pointsToNextLevel: number;
  achievements: Achievement[];
  streaks: {
    login: number;
    lastLoginDate: Date;
  };
  benefitsUsed: {
    partnerId: string;
    benefitId: string;
    usageDate: Date;
    pointsEarned: number;
  }[];
}

// Modelo de Conquista
interface Achievement {
  id: string;
  title: string;
  description: string;
  isUnlocked: boolean;
  unlockedDate?: Date;
  pointsRewarded: number;
  icon: string;
  category: 'engagement' | 'exploration' | 'loyalty' | 'social';
}

// Modelo de Nível
interface JourneyLevel {
  level: number;
  name: string; // Bronze, Prata, etc.
  minPoints: number;
  maxPoints: number;
  benefits: string[];
  icon: string;
  color: string;
}
```

### Componentes React

O sistema utiliza componentes React específicos:

- `JourneyProgressCard`: Exibe o progresso da jornada
- `AchievementsList`: Lista as conquistas do usuário
- `LevelBadge`: Exibe o nível atual do usuário
- `PointsCounter`: Mostra os pontos acumulados
- `BenefitsList`: Lista benefícios disponíveis por nível

### Hooks Personalizados

- `useJourney`: Gerencia o estado da jornada do usuário
- `useAchievements`: Controla as conquistas do usuário
- `useLevelBenefits`: Obtém benefícios disponíveis para o nível atual

## Mecânicas de Engajamento

### Streaks (Sequências)

O sistema incentiva o uso contínuo através de sequências:

- **Login Diário**: Pontos extras por logins em dias consecutivos
- **Uso Semanal**: Recompensas por usar a plataforma toda semana
- **Combo de Benefícios**: Pontos bônus por usar múltiplos benefícios

### Desafios Semanais

Desafios temporários que oferecem pontos extras:

- Visitar determinado número de parceiros
- Usar benefícios específicos
- Completar ações dentro de um prazo

### Eventos Especiais

Eventos sazonais com mecânicas especiais:

- Pontuação dobrada em datas comemorativas
- Conquistas exclusivas por tempo limitado
- Níveis temporários com benefícios especiais

## Notificações e Feedback

O sistema fornece feedback constante:

- **Notificações Push**: Para novos níveis e conquistas
- **Animações**: Ao ganhar pontos ou subir de nível
- **Emails**: Resumos semanais de progresso
- **Feed de Atividades**: Histórico visual de ações e recompensas

## Considerações Futuras

- Implementação de um sistema de missões diárias
- Integração com redes sociais para compartilhamento de conquistas
- Implementação de rankings e competições entre usuários
- Sistema de recompensas físicas para níveis mais altos
- Personalização da jornada baseada em interesses do usuário