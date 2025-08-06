async function runDemo(){
  const file = document.getElementById('videoInput').files[0];
  if(!file) return alert('Select a video');
  const form = new FormData(); form.append('file',file);
  const up=await fetch('/api/upload_video',{method:'POST',body:form});
  const cur=await up.json();
  const slot={start:parseFloat(document.getElementById('startInput').value)||0,duration:parseFloat(document.getElementById('durInput').value)||5};
  const persona={interests:['gaming','tech','performance']};
  const rb=await fetch('/api/rank_and_blend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({video_id:cur.video_id,ext:cur.ext,persona,slot})});
  const res=await rb.json();
  document.getElementById('player').src=res.video_url;
  document.getElementById('decision').innerText=res.decision;
}
document.getElementById('uploadBtn').onclick=runDemo;