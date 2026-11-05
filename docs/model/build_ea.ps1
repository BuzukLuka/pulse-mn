# Enterprise Architect загварт Pulse.mn v2 (хэрэгжсэн байдлаар) багцуудыг нэмнэ.
# 32 битийн PowerShell-ээр ажиллуулна (EA нь 32 бит):
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -File build_ea.ps1 -feap pulse.mn.v2.feap -json pulse_model.json
param([string]$feap, [string]$json)
$ErrorActionPreference = "Stop"
$m = Get-Content $json -Raw -Encoding UTF8 | ConvertFrom-Json
$r = New-Object -ComObject EA.Repository
if (-not $r.OpenFile($feap)) { throw "Нээж чадсангүй: $($r.GetLastError())" }
$proj = $r.GetProjectInterface()

function NewPkg($parent, $name) {
  foreach ($p in $parent.Packages) { if ($p.Name -eq $name) { [void]$parent.Packages.DeleteAt([int]$p.PackageID, $false) } }
  [void]$parent.Packages.Refresh()
  $p = $parent.Packages.AddNew($name, "Package"); [void]$p.Update(); [void]$parent.Packages.Refresh(); return $p
}
function NewEl($pkg, $name, $type, $stereo = "", $notes = "") {
  $e = $pkg.Elements.AddNew($name, $type); if ($stereo) { $e.Stereotype = $stereo }; if ($notes) { $e.Notes = $notes }
  [void]$e.Update(); return $e
}
function Link($a, $b, $type, $name = "", $srcCard = "", $dstCard = "", $guard = "") {
  $c = $a.Connectors.AddNew($name, $type); $c.SupplierID = $b.ElementID
  if ($srcCard) { $c.ClientEnd.Cardinality = $srcCard }; if ($dstCard) { $c.SupplierEnd.Cardinality = $dstCard }
  if ($guard) { $c.TransitionGuard = $guard }
  [void]$c.Update(); return $c
}
function NewDiagram($pkg, $name, $type, $elements) {
  $d = $pkg.Diagrams.AddNew($name, $type); [void]$d.Update()
  $i = 0
  foreach ($e in $elements) {
    $x = 20 + ($i % 6) * 190; $y = 20 + [math]::Floor($i / 6) * 110
    $o = $d.DiagramObjects.AddNew("l=$x;r=$($x+160);t=$y;b=$($y+70);", ""); $o.ElementID = $e.ElementID; [void]$o.Update(); $i++
  }
  [void]$d.Update()
  $proj.LayoutDiagramEx($proj.GUIDtoXML($d.DiagramGUID), 0, 4, 30, 30, $true) | Out-Null
  return $d
}

$root = $null
foreach ($p in $r.Models.GetAt(0).Packages) { if ($p.Name -eq "Pulse.mn") { $root = $p } }
if (-not $root) { throw "Pulse.mn багц олдсонгүй" }

# ---------- 08 Requirements ----------
$req = NewPkg $root "08 Requirements (шаардлага v2)"
$reqEl = @{}
$prio = @{ "Өндөр" = "High"; "Дунд" = "Medium"; "Бага" = "Low" }
foreach ($q in $m.requirements) {
  $e = NewEl $req ("R{0:D2} {1}" -f $q.no, $q.name) "Requirement" $q.type ("{0}`r`nФункц: {1}`r`nОролцогч: {2}`r`nХэрэгжилт: {3}" -f $q.detail, $q.function, $q.actor, $q.impl)
  $e.Status = $q.status; $e.Priority = $prio[$q.priority]; [void]$e.Update()
  $reqEl[[int]$q.no] = $e
}
NewDiagram $req "Шаардлага (хэрэгжилтийн төлөвтэй)" "Custom" ($reqEl.Values) | Out-Null

# ---------- 04 Use Case v2 ----------
$uc = NewPkg $root "04 Use Case (v2 — хэрэгжсэн)"
$act = @{}
foreach ($a in $m.actors.PSObject.Properties) { $act[$a.Name] = NewEl $uc $a.Name "Actor" "" $a.Value }
$ucEls = @()
foreach ($u in $m.use_cases) {
  $e = NewEl $uc $u.name "UseCase"
  foreach ($a in $u.actors) { Link $act[$a] $e "Association" | Out-Null }
  foreach ($n in $u.reqs) { Link $e $reqEl[[int]$n] "Realisation" | Out-Null }
  $ucEls += $e
}
NewDiagram $uc "Pulse.mn v2 — Use Case" "Use Case" (@($act.Values) + $ucEls) | Out-Null

# ---------- 05 Activity v2 ----------
$ac = NewPkg $root "05 Activity (v2)"
foreach ($kv in $m.activities.PSObject.Properties) {
  $p = NewPkg $ac $kv.Name
  $steps = @($kv.Value)
  $start = NewEl $p "Эхлэл" "StateNode"; $start.Subtype = 100; [void]$start.Update()
  $els = @()
  foreach ($s in $steps) {
    switch ($s[0]) {
      "action" { $els += NewEl $p $s[1] "Action" }
      "decision" { $els += NewEl $p $s[1] "Decision" }
      "final" { $f = NewEl $p $s[1] "StateNode"; $f.Subtype = 101; [void]$f.Update(); $els += $f }
    }
  }
  # Шийдвэрийн салаа: нэг шийдвэрийн салаа болох дараалсан алхмууд салааны төгсгөлийн дараагийн алхам руу нийлнэ
  $branchMax = @{}
  for ($i = 0; $i -lt $steps.Count; $i++) {
    if ($steps[$i][0] -eq "decision") {
      $targets = @($steps[$i][2] | ForEach-Object { [int]$_[1] }); $mx = ($targets | Measure-Object -Maximum).Maximum
      foreach ($t in $targets) { $branchMax[$t] = $mx }
    }
  }
  Link $start $els[0] "ControlFlow" | Out-Null
  for ($i = 0; $i -lt $steps.Count; $i++) {
    $kind = $steps[$i][0]
    if ($kind -eq "decision") { foreach ($g in $steps[$i][2]) { Link $els[$i] $els[[int]$g[1]] "ControlFlow" "" "" "" $g[0] | Out-Null } }
    elseif ($kind -eq "action") {
      $next = $i + 1
      if ($branchMax.ContainsKey($i) -and $branchMax.ContainsKey($next) -and $branchMax[$i] -eq $branchMax[$next]) { $next = $branchMax[$i] + 1 }
      if ($next -lt $els.Count) { Link $els[$i] $els[$next] "ControlFlow" | Out-Null }
    }
  }
  NewDiagram $p $kv.Name "Activity" (@($start) + $els) | Out-Null
}

# ---------- 06 Class — домэйн модель ----------
$cl = NewPkg $root "06 Class (домэйн модель)"
$cls = @{}
foreach ($c in $m.classes) {
  $e = NewEl $cl $c.name "Class" "" $c.note
  foreach ($at in $c.attrs) { $a = $e.Attributes.AddNew($at[0], $at[1]); [void]$a.Update() }
  [void]$e.Attributes.Refresh(); $cls[$c.name] = $e
}
foreach ($as in $m.associations) { Link $cls[$as[0]] $cls[$as[1]] "Association" $as[2] $as[3] $as[4] | Out-Null }
NewDiagram $cl "Домэйн модель (Django models)" "Logical" ($cls.Values) | Out-Null

# ---------- 07 Deployment ----------
$dp = NewPkg $root "07 Deployment"
$nodes = @{}
foreach ($n in $m.deployment.nodes) { $nodes[$n] = NewEl $dp $n "Node" }
foreach ($l in $m.deployment.links) { Link $nodes[$l[0]] $nodes[$l[1]] "Association" $l[2] | Out-Null }
NewDiagram $dp "Байршуулалт (Vercel, Neon, Blob)" "Deployment" ($nodes.Values) | Out-Null

[void]$root.Packages.Refresh()
$r.CloseFile(); $r.Exit()
"OK: $($m.requirements.Count) шаардлага, $($m.use_cases.Count) use case, $($m.classes.Count) класс"
