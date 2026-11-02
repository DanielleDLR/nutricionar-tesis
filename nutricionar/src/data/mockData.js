/* =====================================================
   Mock data — Nutricionar · Plataforma Predictiva
   Basado en distribuciones sintéticas del piloto Maule
   ===================================================== */

export const COMUNAS_MAULE = [
  { cod:"07101", nombre:"Talca",            lat:-35.4264, lon:-71.6553, n:264, pct:28.4, nivel:"alto" },
  { cod:"07102", nombre:"Constitución",     lat:-35.3329, lon:-72.4116, n:72,  pct:32.1, nivel:"alto" },
  { cod:"07103", nombre:"Curepto",          lat:-35.0901, lon:-72.0231, n:36,  pct:41.7, nivel:"critico" },
  { cod:"07104", nombre:"Empedrado",        lat:-35.5950, lon:-72.2817, n:24,  pct:45.8, nivel:"critico" },
  { cod:"07105", nombre:"Maule",            lat:-35.5167, lon:-71.7167, n:48,  pct:22.9, nivel:"medio" },
  { cod:"07106", nombre:"Pelarco",          lat:-35.4500, lon:-71.4667, n:24,  pct:38.2, nivel:"alto" },
  { cod:"07107", nombre:"Pencahue",         lat:-35.3833, lon:-71.8167, n:24,  pct:36.5, nivel:"alto" },
  { cod:"07108", nombre:"Río Claro",        lat:-35.2333, lon:-71.2500, n:24,  pct:35.4, nivel:"alto" },
  { cod:"07109", nombre:"San Clemente",     lat:-35.5333, lon:-71.4833, n:48,  pct:26.8, nivel:"alto" },
  { cod:"07110", nombre:"San Rafael",       lat:-35.3000, lon:-71.5333, n:24,  pct:33.3, nivel:"alto" },
  { cod:"07201", nombre:"Cauquenes",        lat:-35.9667, lon:-72.3167, n:60,  pct:30.5, nivel:"alto" },
  { cod:"07202", nombre:"Chanco",           lat:-35.7333, lon:-72.5333, n:24,  pct:39.2, nivel:"alto" },
  { cod:"07203", nombre:"Pelluhue",         lat:-35.8167, lon:-72.5833, n:24,  pct:28.7, nivel:"alto" },
  { cod:"07301", nombre:"Curicó",           lat:-34.9854, lon:-71.2386, n:168, pct:24.2, nivel:"medio" },
  { cod:"07302", nombre:"Hualañé",          lat:-34.9750, lon:-71.8094, n:24,  pct:37.5, nivel:"alto" },
  { cod:"07303", nombre:"Licantén",         lat:-34.9833, lon:-72.0000, n:24,  pct:32.4, nivel:"alto" },
  { cod:"07304", nombre:"Molina",           lat:-35.1167, lon:-71.2833, n:60,  pct:23.8, nivel:"medio" },
  { cod:"07305", nombre:"Rauco",            lat:-34.9333, lon:-71.3667, n:24,  pct:29.6, nivel:"alto" },
  { cod:"07306", nombre:"Romeral",          lat:-34.9667, lon:-71.1167, n:24,  pct:27.8, nivel:"alto" },
  { cod:"07307", nombre:"Sagrada Familia",  lat:-35.0667, lon:-71.3833, n:24,  pct:25.4, nivel:"alto" },
  { cod:"07308", nombre:"Teno",             lat:-34.8667, lon:-71.1667, n:36,  pct:21.5, nivel:"medio" },
  { cod:"07309", nombre:"Vichuquén",        lat:-34.8833, lon:-72.0500, n:24,  pct:42.3, nivel:"critico" },
  { cod:"07401", nombre:"Linares",          lat:-35.8456, lon:-71.5944, n:120, pct:25.7, nivel:"alto" },
  { cod:"07402", nombre:"Colbún",           lat:-35.7000, lon:-71.4167, n:24,  pct:31.6, nivel:"alto" },
  { cod:"07403", nombre:"Longaví",          lat:-36.0167, lon:-71.6833, n:24,  pct:34.8, nivel:"alto" },
  { cod:"07404", nombre:"Parral",           lat:-36.1444, lon:-71.8264, n:48,  pct:27.9, nivel:"alto" },
  { cod:"07405", nombre:"Retiro",           lat:-36.0500, lon:-71.7667, n:24,  pct:30.2, nivel:"alto" },
  { cod:"07406", nombre:"San Javier",       lat:-35.5833, lon:-71.7333, n:36,  pct:26.4, nivel:"alto" },
  { cod:"07407", nombre:"Villa Alegre",     lat:-35.6833, lon:-71.7500, n:24,  pct:32.7, nivel:"alto" },
  { cod:"07408", nombre:"Yerbas Buenas",    lat:-35.7833, lon:-71.5833, n:24,  pct:28.6, nivel:"alto" },
];

export const RISK_COLORS = {
  critico: "#8B1A1A",
  alto:    "#C76123",
  medio:   "#D9A847",
  bajo:    "#2C5530",
};

// KPI_DATA: fallback cuando la API no responde.
// Valores calibrados con dataset sintetico piloto (seed=42, n=1200, IPRN).
// La API en vivo reemplaza estos valores via buildKpis() en KPIStrip.jsx.
export const KPI_DATA = [
  { label: "Riesgo alto · Maule",       value: "29,5", unit: "%", delta: "354 personas (piloto)",   deltaType: "neutral", type: "danger" },
  { label: "Riesgo critico · Maule",    value: "16,7", unit: "%", delta: "200 personas (piloto)",   deltaType: "neutral", type: "danger" },
  { label: "Inseg. alimentaria",        value: "23,7", unit: "%", delta: "moderada + severa · IPRN", deltaType: "neutral", type: "neutral" },
  { label: "Beneficiarios PACAM",       value: "39,4", unit: "%", delta: "del total evaluado",       deltaType: "neutral", type: "neutral" },
];

export const NON_RETIRERS = [
  { id: 1, nombre: "María del Carmen Reyes S.", rut: "14.223.***-*", zona: "Curepto rural", edad: 82, nivel: "critico", dias: 62, motivo: "Movilidad reducida", ultimaVisita: "15 ene 2025", visitaColor: "" },
  { id: 2, nombre: "Juan Esteban Morales V.",   rut: "8.445.***-*",  zona: "Curepto rural", edad: 88, nivel: "critico", dias: 91, motivo: "Distancia",          ultimaVisita: "03 dic 2024", visitaColor: "" },
  { id: 3, nombre: "Rosa Elena Gutiérrez P.",   rut: "9.112.***-*",  zona: "Curepto urbano", edad: 78, nivel: "alto",    dias: 45, motivo: "Desconocimiento",    ultimaVisita: "28 feb 2025", visitaColor: "" },
  { id: 4, nombre: "Pedro Antonio Sepúlveda M.", rut: "7.998.***-*", zona: "Curepto rural", edad: 91, nivel: "critico", dias: 74, motivo: "Movilidad reducida", ultimaVisita: "Sin visitas",  visitaColor: "critico" },
  { id: 5, nombre: "Carmen Gloria Fuentes R.",  rut: "10.334.***-*", zona: "Curepto rural", edad: 75, nivel: "alto",    dias: 38, motivo: "Calidad percibida",  ultimaVisita: "10 mar 2025", visitaColor: "" },
  { id: 6, nombre: "Héctor Osvaldo Bravo L.",   rut: "6.887.***-*",  zona: "Curepto rural", edad: 85, nivel: "critico", dias: 55, motivo: "Distancia",          ultimaVisita: "22 ene 2025", visitaColor: "" },
  { id: 7, nombre: "Ana María Contreras D.",    rut: "12.556.***-*", zona: "Curepto urbano", edad: 72, nivel: "medio",   dias: 31, motivo: "Desconocimiento",    ultimaVisita: "Ayer",        visitaColor: "bajo" },
  { id: 8, nombre: "Luis Alberto Ramírez O.",   rut: "11.223.***-*", zona: "Curepto rural", edad: 80, nivel: "alto",    dias: 42, motivo: "Movilidad reducida", ultimaVisita: "Sin visitas",  visitaColor: "critico" },
];

export const PATIENT_DETAIL = {
  id: 1,
  nombre: "María del Carmen Reyes Soto",
  iniciales: "MR",
  rut: "14.223.***-*",
  edad: 82,
  sexo: "Mujer",
  comuna: "Curepto (07103)",
  zona: "Rural",
  tramoRSH: "A",
  scoreRiesgo: 0.82,
  nivelRiesgo: "critico",
  recomendacion: "Derivar a nutricionista APS de forma prioritaria",
  telefono: "+56 9 7234 ****",
  direccion: "Camino Vecinal s/n, Curepto, Maule",
  // iprnScore reemplaza a mnaPuntaje: el IPRN es el proxy observable
  // (0-1) construido desde variables de encuesta disponibles en ENS/CASEN.
  // El puntaje MNA clinico (0-30) NO esta disponible en datos reales.
  iprnScore: 0.82,
  estadoNutricional: "critico",
  estadoNutricionalLabel: "Riesgo critico (IPRN >= 0.62)",
  comorbilidades: [
    { nombre: "Diabetes mellitus",   valor: "Si",  nivel: "critico" },
    { nombre: "Hipertension",         valor: "Si",  nivel: "alto" },
    { nombre: "Depresion",            valor: "Si",  nivel: "alto" },
    { nombre: "Limitacion fisica",    valor: "Si",  nivel: "critico" },
    { nombre: "Osteoporosis",         valor: "Si",  nivel: "alto" },
    { nombre: "Perdida dentaria",     valor: "Si",  nivel: "alto" },
    { nombre: "Dificultad visual",    valor: "Si",  nivel: "alto" },
    { nombre: "Necesita ayuda AVD",   valor: "Si",  nivel: "critico" },
  ],
  laboratorio: [
    { nombre: "Albumina serica",   valor: "2.9 g/dL",  nota: "(<3.5)", nivel: "critico" },
    { nombre: "Hemoglobina",       valor: "10.8 g/dL", nota: "(<12)",  nivel: "alto" },
    { nombre: "Glucosa ayunas",    valor: "178 mg/dL", nota: "",       nivel: "alto" },
  ],
  // factoresRiesgo: feature importance del modelo RF (IPRN).
  // circ_pantorrilla es la feature mas importante (24.2%), seguida de imc (20.8%).
  factoresRiesgo: [
    { nombre: "Circ. pantorrilla baja",   pct: 88, nivel: "critico" },
    { nombre: "Limitacion fisica",        pct: 74, nivel: "critico" },
    { nombre: "Inseg. alimentaria severa",pct: 65, nivel: "alto" },
    { nombre: "Depresion",                pct: 52, nivel: "alto" },
    { nombre: "Ingreso per capita bajo",  pct: 40, nivel: "medio" },
  ],
  pacamEstado: "alto",
  pacamEstadoLabel: "Beneficiaria inscrita · No retira",
  pacamMotivoDeclarado: "Movilidad reducida",
  pacamHistorial: [
    { mes: "Marzo 2025",     retiró: false },
    { mes: "Febrero 2025",   retiró: false },
    { mes: "Enero 2025",     retiró: true,  nota: "Retiro por familiar (hija)" },
    { mes: "Diciembre 2024", retiró: false },
    { mes: "Noviembre 2024", retiró: true  },
    { mes: "Octubre 2024",   retiró: false },
  ],
  socioeconomico: {
    tramo: "A (máx. vulnerable)",
    ingreso: "$62.000 CLP",
    pobreza: "Extrema",
    pobrezaMulti: "Sí (4 carencias)",
    hogar: "1 (vive sola)",
    estadoCivil: "Viuda",
    vivienda: "Mediagua",
    pension: "PBS $214.000",
    carencias: ["Educación", "Salud", "Vivienda", "Redes"],
  },
};
