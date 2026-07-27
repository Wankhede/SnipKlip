export const BACKEND_URL = process.env.SNIPKLIP_BACKEND_URL || 'http://127.0.0.1:8082';
export const FRONTEND_URL = process.env.SNIPKLIP_FRONTEND_URL || 'http://127.0.0.1:8083';

/** Seeded admin — username `admin` or email both work via EmailBackend */
export const ADMIN_USER = process.env.SNIPKLIP_ADMIN_USER || 'admin';
export const ADMIN_EMAIL = process.env.SNIPKLIP_ADMIN_EMAIL || 'admin@snipklip.local';
export const ADMIN_PASSWORD = process.env.SNIPKLIP_ADMIN_PASSWORD || 'Admin@123';

/** Seeded Staff employee */
export const EMPLOYEE_USER =
  process.env.SNIPKLIP_EMPLOYEE_USER || process.env.SNIPKLIP_EMPLOYEE_EMAIL || 'employee@snipklip.local';
export const EMPLOYEE_EMAIL = process.env.SNIPKLIP_EMPLOYEE_EMAIL || 'employee@snipklip.local';
export const EMPLOYEE_PASSWORD = process.env.SNIPKLIP_EMPLOYEE_PASSWORD || 'Employee@123';

/** Seeded Customer / end-user */
export const CUSTOMER_USER =
  process.env.SNIPKLIP_CUSTOMER_USER || process.env.SNIPKLIP_CUSTOMER_EMAIL || 'customer@snipklip.local';
export const CUSTOMER_EMAIL = process.env.SNIPKLIP_CUSTOMER_EMAIL || 'customer@snipklip.local';
export const CUSTOMER_PASSWORD = process.env.SNIPKLIP_CUSTOMER_PASSWORD || 'Customer@123';

/** Known seeded salon/branch used when admin login returns -1 context */
export const DEFAULT_SALON_ID = Number(process.env.SNIPKLIP_SALON_ID || 3);
export const DEFAULT_BRANCH_ID = Number(process.env.SNIPKLIP_BRANCH_ID || 1);
