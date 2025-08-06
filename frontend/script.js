let current={};

async function runDemo(){
  const vidEl = document.getElementById('videoInput');
  if(!vidEl.files.length) return alert('Select a video');
  const form = new FormData(); form.append('file',vidEl.files[0]);
  const up = await fetch('/api/upload_video',{method:'POST',body:form});
  current = await up.json();
  const slot={start:parseFloat(document.getElementById('startInput').value)||0,duration:parseFloat(document.getElementById('durInput').value)||5};
  const persona={interests:['gaming','tech','performance']};
  const rb = await fetch('/api/rank_and_blend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({video_id:current.video_id,ext:current.ext,persona,slot})});
  const out=await rb.json();
  document.getElementById('player').src=out.video_url;
  document.getElementById('decision').innerText=out.decision;
}
document.getElementById('uploadBtn').onclick=runDemo;