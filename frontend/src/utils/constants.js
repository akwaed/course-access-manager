export const UK_COLORS = {
  wildcatBlue: '#0033A0',
  bluegrass: '#1E8AFF',
  midnight: '#1B365D',
  sky: '#B1C9E8',
  white: '#FFFFFF',
  goldenrod: '#FFDC00',
  sunset: '#FFA360',
  riverGreen: '#4CBCC0',
  coolNeutral: '#DCDDDE',
  warmNeutral: '#D6D2C4',
  black: '#000000'
};

export const API_BASE_URL = process.env.VITE_API_URL || '/tcecontacts/api';

export const USER_ROLES = {
  SYSTEM_ADMIN: 'System Admin',
  COLLEGE_PRIMARY: 'College Primary Contact',
  DEPARTMENT: 'Department Contact'
};

export const CONTACT_TYPES = {
  COLLEGE: 'College',
  DEPARTMENT: 'Department',
  COURSE: 'Course Coordinator'
};

export const LEVEL_TYPES = {
  REPORT: 'Report Viewer',
  SOURCE: 'Source Viewer'
};
