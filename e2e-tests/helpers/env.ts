export const BACKEND_URL = process.env.SNIPKLIP_BACKEND_URL || 'http://127.0.0.1:8082';
export const FRONTEND_URL = process.env.SNIPKLIP_FRONTEND_URL || 'http://127.0.0.1:8083';
export const ADMIN_USER = process.env.SNIPKLIP_ADMIN_USER || 'admin';
export const ADMIN_PASSWORD = process.env.SNIPKLIP_ADMIN_PASSWORD || 'Admin@123';

/** Known seeded salon/branch used when admin login returns -1 context */
export const DEFAULT_SALON_ID = Number(process.env.SNIPKLIP_SALON_ID || 3);
export const DEFAULT_BRANCH_ID = Number(process.env.SNIPKLIP_BRANCH_ID || 1);
