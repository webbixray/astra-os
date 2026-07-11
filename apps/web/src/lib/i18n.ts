export type Locale = 'en' | 'es' | 'fr' | 'de' | 'ja' | 'zh';

export interface Translation {
  [key: string]: string | Translation;
}

const translations: Record<Locale, Translation> = {
  en: {
    common: {
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      create: 'Create',
      search: 'Search',
      loading: 'Loading...',
      noResults: 'No results found',
      confirm: 'Confirm',
      back: 'Back',
      next: 'Next',
      finish: 'Finish',
      close: 'Close',
      open: 'Open',
      yes: 'Yes',
      no: 'No',
      ok: 'OK',
      error: 'Error',
      success: 'Success',
      warning: 'Warning',
      info: 'Info',
    },
    nav: {
      dashboard: 'Dashboard',
      campaigns: 'Campaigns',
      content: 'Content',
      analytics: 'Analytics',
      workflows: 'Workflows',
      settings: 'Settings',
      team: 'Team',
      help: 'Help',
    },
    auth: {
      login: 'Log in',
      logout: 'Log out',
      signUp: 'Sign up',
      email: 'Email',
      password: 'Password',
      forgotPassword: 'Forgot password?',
      resetPassword: 'Reset password',
    },
    dashboard: {
      welcome: 'Welcome back',
      overview: 'Overview',
      recentActivity: 'Recent Activity',
      quickActions: 'Quick Actions',
    },
    campaigns: {
      title: 'Campaigns',
      create: 'Create Campaign',
      name: 'Campaign Name',
      status: 'Status',
      startDate: 'Start Date',
      endDate: 'End Date',
      budget: 'Budget',
    },
    content: {
      title: 'Content',
      create: 'Create Content',
      title_: 'Title',
      type: 'Type',
      author: 'Author',
      publishedAt: 'Published At',
    },
    analytics: {
      title: 'Analytics',
      overview: 'Overview',
      traffic: 'Traffic',
      conversions: 'Conversions',
      revenue: 'Revenue',
    },
  },
  es: {
    common: {
      save: 'Guardar',
      cancel: 'Cancelar',
      delete: 'Eliminar',
      edit: 'Editar',
      create: 'Crear',
      search: 'Buscar',
      loading: 'Cargando...',
      noResults: 'No se encontraron resultados',
      confirm: 'Confirmar',
      back: 'Atrás',
      next: 'Siguiente',
      finish: 'Finalizar',
      close: 'Cerrar',
      open: 'Abrir',
      yes: 'Sí',
      no: 'No',
      ok: 'Aceptar',
      error: 'Error',
      success: 'Éxito',
      warning: 'Advertencia',
      info: 'Información',
    },
    nav: {
      dashboard: 'Panel',
      campaigns: 'Campañas',
      content: 'Contenido',
      analytics: 'Analítica',
      workflows: 'Flujos de trabajo',
      settings: 'Configuración',
      team: 'Equipo',
      help: 'Ayuda',
    },
    auth: {
      login: 'Iniciar sesión',
      logout: 'Cerrar sesión',
      signUp: 'Registrarse',
      email: 'Correo electrónico',
      password: 'Contraseña',
      forgotPassword: '¿Olvidaste tu contraseña?',
      resetPassword: 'Restablecer contraseña',
    },
    dashboard: {
      welcome: 'Bienvenido de nuevo',
      overview: 'Resumen',
      recentActivity: 'Actividad reciente',
      quickActions: 'Acciones rápidas',
    },
    campaigns: {
      title: 'Campañas',
      create: 'Crear campaña',
      name: 'Nombre de la campaña',
      status: 'Estado',
      startDate: 'Fecha de inicio',
      endDate: 'Fecha de fin',
      budget: 'Presupuesto',
    },
    content: {
      title: 'Contenido',
      create: 'Crear contenido',
      title_: 'Título',
      type: 'Tipo',
      author: 'Autor',
      publishedAt: 'Publicado el',
    },
    analytics: {
      title: 'Analítica',
      overview: 'Resumen',
      traffic: 'Tráfico',
      conversions: 'Conversiones',
      revenue: 'Ingresos',
    },
  },
  fr: {
    common: {
      save: 'Enregistrer',
      cancel: 'Annuler',
      delete: 'Supprimer',
      edit: 'Modifier',
      create: 'Créer',
      search: 'Rechercher',
      loading: 'Chargement...',
      noResults: 'Aucun résultat trouvé',
      confirm: 'Confirmer',
      back: 'Retour',
      next: 'Suivant',
      finish: 'Terminer',
      close: 'Fermer',
      open: 'Ouvrir',
      yes: 'Oui',
      no: 'Non',
      ok: 'OK',
      error: 'Erreur',
      success: 'Succès',
      warning: 'Avertissement',
      info: 'Information',
    },
    nav: {
      dashboard: 'Tableau de bord',
      campaigns: 'Campagnes',
      content: 'Contenu',
      analytics: 'Analytique',
      workflows: 'Flux de travail',
      settings: 'Paramètres',
      team: 'Équipe',
      help: 'Aide',
    },
    auth: {
      login: 'Se connecter',
      logout: 'Se déconnecter',
      signUp: "S'inscrire",
      email: 'E-mail',
      password: 'Mot de passe',
      forgotPassword: 'Mot de passe oublié?',
      resetPassword: 'Réinitialiser le mot de passe',
    },
    dashboard: {
      welcome: 'Bon retour',
      overview: 'Aperçu',
      recentActivity: 'Activité récente',
      quickActions: 'Actions rapides',
    },
    campaigns: {
      title: 'Campagnes',
      create: 'Créer une campagne',
      name: 'Nom de la campagne',
      status: 'Statut',
      startDate: 'Date de début',
      endDate: 'Date de fin',
      budget: 'Budget',
    },
    content: {
      title: 'Contenu',
      create: 'Créer du contenu',
      title_: 'Titre',
      type: 'Type',
      author: 'Auteur',
      publishedAt: 'Publié le',
    },
    analytics: {
      title: 'Analytique',
      overview: 'Aperçu',
      traffic: 'Trafic',
      conversions: 'Conversions',
      revenue: 'Revenus',
    },
  },
  de: {
    common: {
      save: 'Speichern',
      cancel: 'Abbrechen',
      delete: 'Löschen',
      edit: 'Bearbeiten',
      create: 'Erstellen',
      search: 'Suchen',
      loading: 'Laden...',
      noResults: 'Keine Ergebnisse gefunden',
      confirm: 'Bestätigen',
      back: 'Zurück',
      next: 'Weiter',
      finish: 'Fertig',
      close: 'Schließen',
      open: 'Öffnen',
      yes: 'Ja',
      no: 'Nein',
      ok: 'OK',
      error: 'Fehler',
      success: 'Erfolg',
      warning: 'Warnung',
      info: 'Information',
    },
    nav: {
      dashboard: 'Dashboard',
      campaigns: 'Kampagnen',
      content: 'Inhalt',
      analytics: 'Analytik',
      workflows: 'Workflows',
      settings: 'Einstellungen',
      team: 'Team',
      help: 'Hilfe',
    },
    auth: {
      login: 'Anmelden',
      logout: 'Abmelden',
      signUp: 'Registrieren',
      email: 'E-Mail',
      password: 'Passwort',
      forgotPassword: 'Passwort vergessen?',
      resetPassword: 'Passwort zurücksetzen',
    },
    dashboard: {
      welcome: 'Willkommen zurück',
      overview: 'Übersicht',
      recentActivity: 'Letzte Aktivität',
      quickActions: 'Schnellaktionen',
    },
    campaigns: {
      title: 'Kampagnen',
      create: 'Kampagne erstellen',
      name: 'Kampagnenname',
      status: 'Status',
      startDate: 'Startdatum',
      endDate: 'Enddatum',
      budget: 'Budget',
    },
    content: {
      title: 'Inhalt',
      create: 'Inhalt erstellen',
      title_: 'Titel',
      type: 'Typ',
      author: 'Autor',
      publishedAt: 'Veröffentlicht am',
    },
    analytics: {
      title: 'Analytik',
      overview: 'Übersicht',
      traffic: 'Verkehr',
      conversions: 'Conversions',
      revenue: 'Umsatz',
    },
  },
  ja: {
    common: {
      save: '保存',
      cancel: 'キャンセル',
      delete: '削除',
      edit: '編集',
      create: '作成',
      search: '検索',
      loading: '読み込み中...',
      noResults: '結果が見つかりません',
      confirm: '確認',
      back: '戻る',
      next: '次へ',
      finish: '完了',
      close: '閉じる',
      open: '開く',
      yes: 'はい',
      no: 'いいえ',
      ok: 'OK',
      error: 'エラー',
      success: '成功',
      warning: '警告',
      info: '情報',
    },
    nav: {
      dashboard: 'ダッシュボード',
      campaigns: 'キャンペーン',
      content: 'コンテンツ',
      analytics: '分析',
      workflows: 'ワークフロー',
      settings: '設定',
      team: 'チーム',
      help: 'ヘルプ',
    },
    auth: {
      login: 'ログイン',
      logout: 'ログアウト',
      signUp: 'サインアップ',
      email: 'メール',
      password: 'パスワード',
      forgotPassword: 'パスワードをお忘れですか？',
      resetPassword: 'パスワードをリセット',
    },
    dashboard: {
      welcome: 'おかえりなさい',
      overview: '概要',
      recentActivity: '最近のアクティビティ',
      quickActions: 'クイックアクション',
    },
    campaigns: {
      title: 'キャンペーン',
      create: 'キャンペーンを作成',
      name: 'キャンペーン名',
      status: 'ステータス',
      startDate: '開始日',
      endDate: '終了日',
      budget: '予算',
    },
    content: {
      title: 'コンテンツ',
      create: 'コンテンツを作成',
      title_: 'タイトル',
      type: 'タイプ',
      author: '著者',
      publishedAt: '公開日',
    },
    analytics: {
      title: '分析',
      overview: '概要',
      traffic: 'トラフィック',
      conversions: 'コンバージョン',
      revenue: '収益',
    },
  },
  zh: {
    common: {
      save: '保存',
      cancel: '取消',
      delete: '删除',
      edit: '编辑',
      create: '创建',
      search: '搜索',
      loading: '加载中...',
      noResults: '未找到结果',
      confirm: '确认',
      back: '返回',
      next: '下一步',
      finish: '完成',
      close: '关闭',
      open: '打开',
      yes: '是',
      no: '否',
      ok: '确定',
      error: '错误',
      success: '成功',
      warning: '警告',
      info: '信息',
    },
    nav: {
      dashboard: '仪表板',
      campaigns: '营销活动',
      content: '内容',
      analytics: '分析',
      workflows: '工作流',
      settings: '设置',
      team: '团队',
      help: '帮助',
    },
    auth: {
      login: '登录',
      logout: '退出',
      signUp: '注册',
      email: '电子邮件',
      password: '密码',
      forgotPassword: '忘记密码？',
      resetPassword: '重置密码',
    },
    dashboard: {
      welcome: '欢迎回来',
      overview: '概览',
      recentActivity: '最近活动',
      quickActions: '快速操作',
    },
    campaigns: {
      title: '营销活动',
      create: '创建营销活动',
      name: '活动名称',
      status: '状态',
      startDate: '开始日期',
      endDate: '结束日期',
      budget: '预算',
    },
    content: {
      title: '内容',
      create: '创建内容',
      title_: '标题',
      type: '类型',
      author: '作者',
      publishedAt: '发布时间',
    },
    analytics: {
      title: '分析',
      overview: '概览',
      traffic: '流量',
      conversions: '转化',
      revenue: '收入',
    },
  },
};

let currentLocale: Locale = 'en';

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  if (typeof window !== 'undefined') {
    localStorage.setItem('astra-locale', locale);
    document.documentElement.lang = locale;
  }
}

export function getLocale(): Locale {
  return currentLocale;
}

export function initializeLocale(): Locale {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('astra-locale') as Locale | null;
    if (stored && translations[stored]) {
      currentLocale = stored;
      return stored;
    }
    const browserLang = navigator.language.split('-')[0] as Locale;
    if (translations[browserLang]) {
      currentLocale = browserLang;
      return browserLang;
    }
  }
  return 'en';
}

function getNestedValue(obj: Translation, path: string): string | undefined {
  const keys = path.split('.');
  let current: Translation | string = obj;

  for (const key of keys) {
    if (typeof current === 'string') return undefined;
    current = current[key];
    if (current === undefined) return undefined;
  }

  return typeof current === 'string' ? current : undefined;
}

export function t(key: string, params?: Record<string, string | number>): string {
  const value = getNestedValue(translations[currentLocale], key)
    || getNestedValue(translations.en, key)
    || key;

  if (!params) return value;

  return Object.entries(params).reduce(
    (result, [paramKey, paramValue]) => result.replace(`{{${paramKey}}}`, String(paramValue)),
    value,
  );
}

export function getAvailableLocales(): { code: Locale; name: string }[] {
  return [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Español' },
    { code: 'fr', name: 'Français' },
    { code: 'de', name: 'Deutsch' },
    { code: 'ja', name: '日本語' },
    { code: 'zh', name: '中文' },
  ];
}
