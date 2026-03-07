/**
 * JAWIR OS — Tool Categories Data
 * All 30 tools organized by category matching the backend
 */

import type { ToolCategory } from '@/types';

export const TOOL_CATEGORIES: ToolCategory[] = [
  {
    id: 'web',
    name: 'Web Search',
    icon: 'travel_explore',
    color: 'text-blue-400',
    tools: [
      { name: 'web_search', description: 'Cari informasi di internet (berita, harga, cuaca)', icon: 'search' },
    ],
  },
  {
    id: 'kicad',
    name: 'KiCad Electronics',
    icon: 'memory',
    color: 'text-green-400',
    tools: [
      { name: 'generate_kicad_schematic', description: 'Generate skematik KiCad dari deskripsi rangkaian', icon: 'schema' },
    ],
  },
  {
    id: 'python',
    name: 'Python Executor',
    icon: 'code',
    color: 'text-yellow-400',
    tools: [
      { name: 'run_python_code', description: 'Jalankan kode Python (30s timeout, sandboxed)', icon: 'terminal' },
    ],
  },
  {
    id: 'gmail',
    name: 'Gmail',
    icon: 'mail',
    color: 'text-red-400',
    tools: [
      { name: 'gmail_search', description: 'Cari email di Gmail', icon: 'search' },
      { name: 'gmail_send', description: 'Kirim email via Gmail', icon: 'send' },
    ],
  },
  {
    id: 'drive',
    name: 'Google Drive',
    icon: 'folder',
    color: 'text-green-500',
    tools: [
      { name: 'drive_search', description: 'Cari file di Google Drive', icon: 'search' },
      { name: 'drive_list', description: 'Daftar isi folder Drive', icon: 'list' },
    ],
  },
  {
    id: 'calendar',
    name: 'Google Calendar',
    icon: 'calendar_month',
    color: 'text-blue-500',
    tools: [
      { name: 'calendar_list_events', description: 'Daftar event mendatang', icon: 'event' },
      { name: 'calendar_create_event', description: 'Buat event baru', icon: 'add_circle' },
    ],
  },
  {
    id: 'sheets',
    name: 'Google Sheets',
    icon: 'table_chart',
    color: 'text-emerald-400',
    tools: [
      { name: 'sheets_read', description: 'Baca data spreadsheet', icon: 'visibility' },
      { name: 'sheets_write', description: 'Tulis data ke spreadsheet', icon: 'edit' },
      { name: 'sheets_create', description: 'Buat spreadsheet baru', icon: 'add' },
    ],
  },
  {
    id: 'docs',
    name: 'Google Docs',
    icon: 'description',
    color: 'text-sky-400',
    tools: [
      { name: 'docs_read', description: 'Baca isi dokumen', icon: 'visibility' },
      { name: 'docs_create', description: 'Buat dokumen baru', icon: 'add' },
    ],
  },
  {
    id: 'forms',
    name: 'Google Forms',
    icon: 'quiz',
    color: 'text-purple-400',
    tools: [
      { name: 'forms_read', description: 'Baca respons form', icon: 'visibility' },
      { name: 'forms_create', description: 'Buat form baru', icon: 'add' },
      { name: 'forms_add_question', description: 'Tambah pertanyaan ke form', icon: 'help' },
    ],
  },
  {
    id: 'desktop',
    name: 'Desktop Control',
    icon: 'desktop_windows',
    color: 'text-orange-400',
    tools: [
      { name: 'open_app', description: 'Buka aplikasi desktop', icon: 'launch' },
      { name: 'open_url', description: 'Buka URL di browser', icon: 'link' },
      { name: 'close_app', description: 'Tutup aplikasi', icon: 'close' },
    ],
  },
  {
    id: 'whatsapp',
    name: 'WhatsApp',
    icon: 'chat',
    color: 'text-green-400',
    tools: [
      { name: 'whatsapp_check_number', description: 'Cek nomor WhatsApp', icon: 'verified' },
      { name: 'whatsapp_list_chats', description: 'Daftar semua chat', icon: 'forum' },
      { name: 'whatsapp_get_messages', description: 'Baca pesan dari chat/grup', icon: 'chat_bubble' },
      { name: 'whatsapp_send_message', description: 'Kirim pesan teks', icon: 'send' },
      { name: 'whatsapp_send_file', description: 'Kirim file/dokumen', icon: 'attach_file' },
      { name: 'whatsapp_list_contacts', description: 'Daftar kontak', icon: 'contacts' },
      { name: 'whatsapp_list_groups', description: 'Daftar grup WhatsApp', icon: 'group' },
    ],
  },
  {
    id: 'polinema',
    name: 'Polinema SIAKAD',
    icon: 'school',
    color: 'text-amber-400',
    tools: [
      { name: 'polinema_get_biodata', description: 'Biodata mahasiswa SIAKAD', icon: 'person' },
      { name: 'polinema_get_akademik', description: 'Absensi, nilai, jadwal, KHS', icon: 'grade' },
      { name: 'polinema_get_lms_assignments', description: 'Tugas & deadline LMS SPADA', icon: 'assignment' },
    ],
  },
  {
    id: 'iot',
    name: 'IoT Integration',
    icon: 'sensors',
    color: 'text-teal-400',
    tools: [
      { name: 'iot_list_devices', description: 'Daftar semua device IoT', icon: 'devices' },
      { name: 'iot_get_device_state', description: 'Status detail device (kipas/alarm)', icon: 'info' },
      { name: 'iot_set_device_state', description: 'Kontrol device (kipas, buzzer)', icon: 'tune' },
      { name: 'iot_get_latest_events', description: 'Event terbaru IoT', icon: 'history' },
      { name: 'iot_ack_or_reset_alarm', description: 'Reset alarm kebakaran', icon: 'notifications_off' },
    ],
  },
];

export const ALL_TOOLS = TOOL_CATEGORIES.flatMap((cat) =>
  cat.tools.map((t) => ({ ...t, category: cat.id, categoryName: cat.name, categoryIcon: cat.icon, categoryColor: cat.color }))
);

export const TOOL_COUNT = ALL_TOOLS.length;
