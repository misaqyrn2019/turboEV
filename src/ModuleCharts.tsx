import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Bootstrap, Row } from './types'
import { CardHead, Empty, Icon } from './components'
import { centerOf, fa, label, mean, minutes, sla, sum } from './utils'

const colors=['#288e72','#74a7da','#e9b35c','#df877d','#96a5b8','#ac9dcc']
const tooltipStyle={borderRadius:9,border:'1px solid #e3eae7',fontFamily:'Vazirmatn',fontSize:11,direction:'rtl' as const}
const statusNames:Record<string,string>={ready:'آماده سرویس',mission:'در مأموریت',charging:'در حال شارژ',out:'خارج از سرویس',maintenance:'نیازمند سرویس'}

export default function ModuleCharts({kind,rows,data}:{kind:string;rows:Row[];data:Bootstrap}){
  if(!['fleets','vehicles','batteries','charges','missions','incidents','tickets'].includes(kind)||!rows.length)return null
  const options=kind==='vehicles'?Object.entries(statusNames).map(([value,label])=>({value,label})):data.catalog[kind].fields.find(f=>f.key==='status')?.options||[]
  const distribution=options.map((o,i)=>({name:o.label,value:rows.filter(r=>(r.effective_status||r.status)===o.value).length,color:colors[i%colors.length]})).filter(s=>s.value>0)
  let chartTitle='توزیع رکوردها بر اساس مرکز';let unit='تعداد';let bars:{name:string;value:number|null}[]=[]
  if(kind==='vehicles'){
    chartTitle='میانگین شارژ به تفکیک مدل';unit='درصد'
    bars=[...new Set(rows.filter(v=>v.type==='electric').map(v=>String(v.model)))].map(model=>{const batteries=data.records.batteries.filter(b=>rows.some(v=>v.model===model&&v.battery_id===b.id));return {name:model,value:mean(batteries,'soc')}})
  }else if(kind==='batteries'){
    chartTitle='توزیع سلامت باتری (SOH)';unit='باتری'
    bars=[{name:'کمتر از ۶۰٪',value:rows.filter(b=>typeof b.soh==='number'&&b.soh<60).length},{name:'۶۰ تا ۸۰٪',value:rows.filter(b=>typeof b.soh==='number'&&b.soh>=60&&b.soh<80).length},{name:'۸۰ تا ۹۰٪',value:rows.filter(b=>typeof b.soh==='number'&&b.soh>=80&&b.soh<90).length},{name:'۹۰ تا ۱۰۰٪',value:rows.filter(b=>typeof b.soh==='number'&&b.soh>=90).length}]
  }else if(kind==='incidents'){
    chartTitle='خرابی‌ها به تفکیک نوع';unit='رخداد'
    bars=(data.catalog.incidents.fields.find(f=>f.key==='category')?.options||[]).map(o=>({name:o.label,value:rows.filter(i=>i.category===o.value).length}))
  }else if(kind==='tickets'){
    chartTitle='بار کاری کارشناسان';unit='درخواست باز'
    bars=[...new Set(rows.map(t=>String(t.owner)))].map(owner=>({name:owner,value:rows.filter(t=>t.owner===owner&&t.status!=='closed').length}))
  }else if(kind==='charges'){
    chartTitle='انرژی به تفکیک شارژر';unit='kWh'
    bars=data.records.chargers.filter(c=>rows.some(r=>r.charger_id===c.id)).map(c=>({name:c.code,value:sum(rows.filter(r=>r.charger_id===c.id),'energy_kwh')}))
  }else if(kind==='fleets'){
    chartTitle='تعداد موتور در هر ناوگان';unit='دستگاه'
    bars=rows.map(f=>({name:String(f.name),value:data.records.vehicles.filter(v=>v.fleet_id===f.id).length}))
  }else{
    bars=data.records.centers.filter(c=>rows.some(r=>r.center_id===c.id)).map(c=>({name:String(c.name),value:rows.filter(r=>r.center_id===c.id).length}))
  }
  const critical=kind==='batteries'?rows.filter(b=>b.bms_critical||b.status!=='healthy'||typeof b.temperature==='number'&&b.temperature>=Number(data.settings.high_temperature)):kind==='incidents'?rows.filter(r=>r.severity==='critical'&&!['closed','resolved'].includes(String(r.status))):kind==='vehicles'?rows.filter(r=>Array.isArray(r.readiness_reasons)&&r.readiness_reasons.length):[]
  return <div className="module-charts"><section className="card"><CardHead title="توزیع وضعیت" subtitle="مطابق فیلترهای انتخاب‌شده"/><div className="module-donut"><ResponsiveContainer width="45%" height={170}><PieChart><Pie data={distribution} dataKey="value" innerRadius={40} outerRadius={60} paddingAngle={3} stroke="none" isAnimationActive={false}>{distribution.map(s=><Cell key={s.name} fill={s.color}/>)}</Pie><Tooltip contentStyle={tooltipStyle} formatter={(v,name)=>[fa(Number(v)),name]}/></PieChart></ResponsiveContainer><div className="chart-legend-list">{distribution.map(s=><div key={s.name}><span><i style={{background:s.color}}/>{s.name}</span><b>{fa(s.value)}</b></div>)}</div></div></section><section className="card"><CardHead title={chartTitle} subtitle={unit}/><div className="module-bar" dir="ltr"><ResponsiveContainer width="100%" height="100%"><BarChart data={bars.slice(0,10)} margin={{top:10,right:15,left:-20,bottom:0}}><CartesianGrid vertical={false} stroke="#edf1ed"/><XAxis dataKey="name" tick={{fontSize:9,fill:'#809389'}} axisLine={false} tickLine={false} interval={0} tickFormatter={v=>String(v).length>14?String(v).slice(0,14)+'…':String(v)}/><YAxis axisLine={false} tickLine={false} tick={{fontSize:10,fill:'#8b9c91'}} tickFormatter={v=>fa(Number(v))}/><Tooltip contentStyle={tooltipStyle} formatter={v=>[fa(Number(v)),unit]}/><Bar dataKey="value" fill="#73ad98" radius={[4,4,0,0]} maxBarSize={35} isAnimationActive={false}/></BarChart></ResponsiveContainer></div></section><section className="card"><CardHead title={['fleets','missions'].includes(kind)?'موقعیت ثبت‌شده مراکز':kind==='tickets'?'خلاصه پاسخگویی':kind==='charges'?'وضعیت نوبت‌ها':'موارد نیازمند توجه'} subtitle={['fleets','missions'].includes(kind)?'نمای شماتیک مختصات؛ بدون اتصال GPS':kind==='tickets'?'اهداف اولیه SLA':'بر اساس آخرین اطلاعات ثبت‌شده'}/>{['fleets','missions'].includes(kind)?<CenterPlot centers={data.records.centers.filter(c=>rows.some(r=>centerOf(kind,r,data)===c.id))}/>:kind==='tickets'?<div className="report-measures compact">{[['پاسخ در محدوده هدف',rows.filter(r=>r.responded_at&&sla(r,data).met).length],['عبور از هدف پاسخ',rows.filter(r=>!sla(r,data).met).length],['هنوز در مهلت پاسخ',rows.filter(r=>!r.responded_at&&sla(r,data).met).length]].map(([k,v])=><div key={String(k)}><span>{k}</span><b>{fa(Number(v))}</b></div>)}</div>:kind==='charges'?<div className="report-measures compact"><div><span>شارژرهای آماده</span><b>{fa(data.records.chargers.filter(c=>c.status==='ready'&&!data.records.charges.some(r=>r.charger_id===c.id&&r.status==='charging')).length)}</b></div><div><span>میانگین مدت نوبت کامل</span><b>{fa(mean(rows.filter(r=>r.status==='completed').map(r=>({...r,duration:minutes(r.started_at,r.ended_at)})),'duration'))} دقیقه</b></div><div><span>شارژهای ناموفق</span><b>{fa(rows.filter(r=>r.status==='failed').length)}</b></div></div>:<div className="small-attention">{critical.length?critical.slice(0,3).map(r=><div key={r.id}><span className="tiny-dot amber"/><div><b>{r.code} · {label(r)}</b><small>{kind==='vehicles'?(r.readiness_reasons as string[]).join('، '):kind==='batteries'?String(r.bms_error||'بررسی وضعیت باتری'):String(r.next_action||r.owner)}</small></div></div>):<div className="no-alert"><Icon name="CircleCheck" size={26}/><span>موردی در این نما ثبت نشده است.</span></div>}</div>}</section></div>
}
function CenterPlot({centers}:{centers:Row[]}){
  const valid=centers.filter(c=>typeof c.latitude==='number'&&typeof c.longitude==='number')
  if(!valid.length)return <div className="no-alert"><Icon name="MapPin" size={27}/><span>مختصات مرکز را ثبت کنید.</span></div>
  const lats=valid.map(c=>Number(c.latitude));const lons=valid.map(c=>Number(c.longitude));const minLat=Math.min(...lats)-.08,maxLat=Math.max(...lats)+.08,minLon=Math.min(...lons)-.1,maxLon=Math.max(...lons)+.1
  return <div className="center-plot"><svg viewBox="0 0 320 160" role="img" aria-label="پراکندگی مراکز بر اساس طول و عرض جغرافیایی"><defs><pattern id="mapgrid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M 25 0 L 0 0 0 25" fill="none" stroke="#e4ece5" strokeWidth="1"/></pattern></defs><rect width="320" height="160" fill="#f6f9f5"/><rect width="320" height="160" fill="url(#mapgrid)"/><text x="15" y="18" fill="#839b8a" fontSize="11">N ↑</text>{valid.map((c,i)=>{const x=25+(Number(c.longitude)-minLon)/(maxLon-minLon)*265,y=25+(maxLat-Number(c.latitude))/(maxLat-minLat)*103;return <g key={c.id}><title>{String(c.name)} · {String(c.latitude)}, {String(c.longitude)}</title><circle cx={x} cy={y} r={13} fill="#238b6e18"/><circle cx={x} cy={y} r={6} fill={colors[i%colors.length]} stroke="white" strokeWidth={2}/><text x={x} y={y+23} textAnchor="middle" fontFamily="Vazirmatn" fontSize={8} fill="#5f7d69">{String(c.name)}</text></g>})}</svg></div>
}
