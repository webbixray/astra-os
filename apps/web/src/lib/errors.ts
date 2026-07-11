export interface AppError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: number;
}

export const ErrorCodes = {
  // Auth errors (1xxx)
  AUTH_INVALID_CREDENTIALS: {
    code: 'AUTH_INVALID_CREDENTIALS',
    message: 'Invalid email or password',
    status: 401,
  },
  AUTH_SESSION_EXPIRED: {
    code: 'AUTH_SESSION_EXPIRED',
    message: 'Your session has expired. Please log in again',
    status: 401,
  },
  AUTH_UNAUTHORIZED: {
    code: 'AUTH_UNAUTHORIZED',
    message: 'You do not have permission to perform this action',
    status: 403,
  },
  AUTH_RATE_LIMITED: {
    code: 'AUTH_RATE_LIMITED',
    message: 'Too many login attempts. Please try again later',
    status: 429,
  },

  // Validation errors (2xxx)
  VALIDATION_REQUIRED: {
    code: 'VALIDATION_REQUIRED',
    message: 'This field is required',
    status: 400,
  },
  VALIDATION_INVALID_EMAIL: {
    code: 'VALIDATION_INVALID_EMAIL',
    message: 'Please enter a valid email address',
    status: 400,
  },
  VALIDATION_TOO_SHORT: {
    code: 'VALIDATION_TOO_SHORT',
    message: 'This field is too short',
    status: 400,
  },
  VALIDATION_TOO_LONG: {
    code: 'VALIDATION_TOO_LONG',
    message: 'This field is too long',
    status: 400,
  },

  // API errors (3xxx)
  API_NETWORK_ERROR: {
    code: 'API_NETWORK_ERROR',
    message: 'Unable to connect to the server. Please check your connection',
    status: 0,
  },
  API_TIMEOUT: {
    code: 'API_TIMEOUT',
    message: 'The request took too long. Please try again',
    status: 0,
  },
  API_SERVER_ERROR: {
    code: 'API_SERVER_ERROR',
    message: 'Something went wrong on our end. Please try again later',
    status: 500,
  },
  API_NOT_FOUND: {
    code: 'API_NOT_FOUND',
    message: 'The resource you requested was not found',
    status: 404,
  },

  // Campaign errors (4xxx)
  CAMPAIGN_NOT_FOUND: {
    code: 'CAMPAIGN_NOT_FOUND',
    message: 'Campaign not found',
    status: 404,
  },
  CAMPAIGN_INVALID_STATUS: {
    code: 'CAMPAIGN_INVALID_STATUS',
    message: 'Invalid campaign status transition',
    status: 400,
  },
  CAMPAIGN_BUDGET_EXCEEDED: {
    code: 'CAMPAIGN_BUDGET_EXCEEDED',
    message: 'Campaign budget has been exceeded',
    status: 400,
  },

  // Content errors (5xxx)
  CONTENT_GENERATION_FAILED: {
    code: 'CONTENT_GENERATION_FAILED',
    message: 'Failed to generate content. Please try again',
    status: 500,
  },
  CONTENT_PUBLISH_FAILED: {
    code: 'CONTENT_PUBLISH_FAILED',
    message: 'Failed to publish content',
    status: 500,
  },

  // AI errors (6xxx)
  AI_PROVIDER_UNAVAILABLE: {
    code: 'AI_PROVIDER_UNAVAILABLE',
    message: 'AI service is temporarily unavailable',
    status: 503,
  },
  AI_QUOTA_EXCEEDED: {
    code: 'AI_QUOTA_EXCEEDED',
    message: 'AI usage quota has been exceeded',
    status: 429,
  },
  AI_INVALID_REQUEST: {
    code: 'AI_INVALID_REQUEST',
    message: 'Invalid AI request. Please check your input',
    status: 400,
  },

  // Generic errors (9xxx)
  UNKNOWN_ERROR: {
    code: 'UNKNOWN_ERROR',
    message: 'An unexpected error occurred',
    status: 0,
  },
} as const;

export type ErrorCode = keyof typeof ErrorCodes;

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String((error as { message: unknown }).message);
  }
  return ErrorCodes.UNKNOWN_ERROR.message;
}

export function getErrorDetails(error: unknown): AppError {
  if (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error
  ) {
    return {
      code: String((error as { code: unknown }).code),
      message: String((error as { message: unknown }).message),
      details: 'details' in error ? (error as { details: unknown }).details as Record<string, unknown> : undefined,
      timestamp: Date.now(),
    };
  }

  const message = getErrorMessage(error);
  return {
    code: 'UNKNOWN_ERROR',
    message,
    timestamp: Date.now(),
  };
}

export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.name === 'TypeError' && error.message.includes('fetch');
  }
  return false;
}

export function isAuthError(error: unknown): boolean {
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const status = (error as { status: unknown }).status;
    return status === 401 || status === 403;
  }
  return false;
}
