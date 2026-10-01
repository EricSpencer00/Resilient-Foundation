#!/usr/bin/env python3
'''Specification consistency checks. Not a solver, proof kernel or compiler.'''
from pathlib import Path, PurePosixPath
import argparse,copy,hashlib,json,re,sys
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    def pairs(xs):
        d={}
        for k,v in xs:
            if k in d:raise ValueError('Duplicate JSON key: '+k)
            d[k]=v
        return d
    return json.loads((ROOT/path).read_text(),object_pairs_hook=pairs)
def require(condition,message):
    if not condition:raise ValueError(message)
def safe_path(p):
    q=PurePosixPath(p)
    return not q.is_absolute() and '..' not in q.parts and bool(q.parts)
def check_work_package_status(w):
    require(w['status'] in ['planned','in_progress'],'Unsupported work-package status; completion needs an acceptance checker')
    if w['status']=='in_progress':
        artifacts=w.get('implementation_artifacts',[])
        require(bool(artifacts),'In-progress work package lacks implementation artifacts')
        require(all(safe_path(p) and (ROOT/p).is_file() for p in artifacts),'Missing or unsafe implementation artifact')
def check_backend_status(route):
    '''Validate recorded experimental progress; never discharge program obligations.'''
    if route['status']=='planned':
        require(route['checker_status']=='planned','Planned route claims an implemented checker')
        return
    require(route['status']=='experimental' and route['checker_status']=='implemented',
            'Released/mechanized backend claim needs its own acceptance gate')
    expected={'scalar-smt':['solver_checked'],'translation-ir':['translation_checked']}
    require(route['id'] in expected and route['evidence_classes']==expected[route['id']],
            'Unsupported backend or inflated evidence class')
    artifacts=route.get('implementation_artifacts',[])
    require(artifacts and all(safe_path(p) and (ROOT/p).is_file() for p in artifacts),'Backend lacks implementation artifacts')
    record=route.get('evidence_report','')
    require(safe_path(record) and (ROOT/record).is_file(),'Backend lacks recorded acceptance run')
    report=load(record)
    require(report['status']=='passed' and report['scope']=='scalar_e2e_conformance' and
            report['policy']=='scalar_source_exact_trusted_rust_v1','Unsupported recorded gate')
    require(report['tests_run']>0 and report['tests_failed']==report['tests_skipped']==0 and
            report['oracle_cases_executed']==5,'Recorded gate failed or skipped')
    require(route['id'] in report['capability_ids'] and report['formal_class']=='solver_checked' and
            report['translation_class']=='translation_checked' and report['native_relation']=='trusted_compilation',
            'Recorded assurance scope differs')
    for group in ['implementation_hashes','test_hashes','driver_hashes','evidence_files']:
        bindings=report.get(group,{})
        require(bindings,'Recorded run lacks '+group)
        for p,digest in bindings.items():
            require(safe_path(p) and (ROOT/p).is_file() and
                    hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,'Stale recorded run: '+p)
    require(set(artifacts)<=set(report['implementation_hashes']),'Implementation not bound by recorded run')
def cyclic(nodes,edges):
    colors={}
    def visit(n):
        if colors.get(n)==1:return True
        if colors.get(n)==2:return False
        colors[n]=1
        for m in edges.get(n,[]):
            if m in nodes and visit(m):return True
        colors[n]=2
        return False
    return any(visit(n) for n in nodes if not colors.get(n))
def infer(expr,params):
    k=expr['kind']; typ=expr['type']
    if k=='int':
        require(-(1<<63)<=int(expr['value'])<(1<<63),'IR literal outside i64')
        actual='i64'
    elif k=='bool':actual='bool'
    elif k=='var':
        require(expr['name'] in params,'Unbound IR variable')
        actual=params[expr['name']]
    elif k=='if':
        require(infer(expr['condition'],params)=='bool','if condition must be bool')
        a=infer(expr['then'],params);b=infer(expr['else'],params)
        require(a==b,'if branch types disagree');actual=a
    elif k=='binary':
        a=infer(expr['left'],params);b=infer(expr['right'],params);op=expr['op']
        require(a==b,'Binary operand types disagree')
        if op in ['and','or']:
            require(a=='bool','Boolean operator type');actual='bool'
        elif op=='eq':actual='bool'
        elif op.endswith('_signed'):
            require(a=='i64','Signed comparison type');actual='bool'
        else:
            require(a=='i64','Machine arithmetic type');actual='i64'
    else:raise ValueError('Unsupported IR node')
    require(typ==actual,'Declared IR type differs from inferred type')
    return actual
def graph_errors(graph):
    out=[];ids=[x['id'] for x in graph['nodes']];nodes=set(ids)
    if len(nodes)!=len(ids):out.append('duplicate_graph_node')
    for edge in graph['edges']:
        if edge['from'] not in nodes or edge['to'] not in nodes:out.append('dangling_graph_edge')
    dep={}
    for edge in graph['edges']:
        if edge['relation']=='depends_on':dep.setdefault(edge['from'],[]).append(edge['to'])
    if cyclic(nodes,dep):out.append('dependency_cycle')
    if any(root not in nodes for root in graph['required_roots']):out.append('missing_graph_root')
    return out
def policy_errors(context):
    b=context['bundle'];r=context['result'];g=context['graph'];l=context['ledger'];p=context['profile']
    out=graph_errors(g)
    if any(not safe_path(a['path']) for a in b['artifacts']):out.append('unsafe_artifact_path')
    if any(x['task_id']!=b['task_id'] for x in [r,g,l]):out.append('task_id_mismatch')
    if r['semantic_profile_id']!=p['id']:out.append('semantic_profile_mismatch')
    if set(r['required_obligation_ids'])!=set(g['required_roots']) or set(b['obligation_ids'])!=set(g['required_roots']):
        out.append('required_roots_mismatch')
    actual={a['id']:a['sha256'] for a in b['artifacts']}
    if any(actual.get(aid)!=digest for aid,digest in r['artifact_hashes'].items()):out.append('artifact_hash_mismatch')
    if l['interpretation_state']=='accepted' and l['unresolved_ambiguities']:out.append('accepted_intent_with_ambiguity')
    if any(x['outcome']=='Proved' for x in [r['formal'],r['translation']]):
        if r['illustrative'] or b['illustrative']:out.append('illustrative_proof_claim')
        else:out.append('actual_checker_unavailable')
    for axis in [r['formal'],r['translation']]:
        if axis['outcome']!='Proved' and axis['evidence_class'] in ['solver_checked','kernel_checked','translation_checked']:
            out.append('status_evidence_mismatch')
    if r['discharged_obligation_ids'] and r['formal']['outcome']!='Proved':out.append('unknown_discharged')
    if r['acceptance']=='Accepted':
        if set(r['discharged_obligation_ids'])!=set(r['required_obligation_ids']) or r['formal']['outcome']!='Proved' or r['translation']['outcome']!='Proved':
            out.append('required_obligation_open')
        # This specification-only checker never accepts actual proof assertions.
        out.append('actual_checker_unavailable')
    if b['execution_authorized'] and r['acceptance']!='Accepted':out.append('execution_without_acceptance')
    return sorted(set(out))
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    schemas={}
    for p in sorted((ROOT/'schemas').glob('*.schema.json')):
        s=load(str(p.relative_to(ROOT)));Draft202012Validator.check_schema(s)
        schemas[p.stem.removesuffix('.schema')]=s
    mapping={'requirement_ledger':'requirements','semantic_profile':'semantic-profile','scalar_program':'program-ir',
      'obligation':'obligation','pipeline_result':'pipeline-result','evidence_graph':'evidence-graph',
      'task_bundle':'task-bundle','eval_run_plan':'eval-run-plan','backend_capabilities':'backend-capabilities'}
    instances=0
    for p in sorted(ROOT.rglob('*.json')):
        if any(x in p.parts for x in ['.git','.venv','artifacts','target']) or p.name=='.validation-report.json':continue
        x=load(str(p.relative_to(ROOT)))
        if isinstance(x,dict) and x.get('kind') in mapping:
            Draft202012Validator(schemas[mapping[x['kind']]]).validate(x);instances+=1
            if x['kind']=='scalar_program':
                f=x['function'];params={p['name']:p['type'] for p in f['params']}
                require(len(params)==len(f['params']),'Duplicate parameter')
                require(infer(f['body'],params)==f['return_type'],'Return type mismatch')
    reg=load('requirements/registry.json')['requirements']
    wps=load('roadmap/work-packages.json')['work_packages']
    rids={r['id'] for r in reg};wids={w['id'] for w in wps}
    require(len(rids)==len(reg),'Duplicate requirement ID');require(len(wids)==len(wps),'Duplicate work package')
    dependencies={}
    for r in reg:
        require((ROOT/r['document']).is_file(),'Missing requirement document: '+r['id'])
        require(r['work_packages'] and set(r['work_packages'])<=wids,'Missing requirement work package')
    for w in wps:
        check_work_package_status(w)
        require(set(w['depends_on'])<=wids and w['id'] not in w['depends_on'],'Invalid work-package dependency')
        require(w['requirement_ids'] and set(w['requirement_ids'])<=rids,'Untraced work package')
        require(all((ROOT/p).is_file() for p in w['documents']),'Missing work-package document')
        for rid in w['requirement_ids']:
            r=next(r for r in reg if r['id']==rid)
            require(w['id'] in r['work_packages'],'Asymmetric requirement traceability')
        dependencies[w['id']]=w['depends_on']
    require(not cyclic(wids,dependencies),'Work-package dependency cycle')
    links=0
    for p in ROOT.rglob('*.md'):
        if any(x in p.parts for x in ['.git','.venv','target']):continue
        for dest in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',dest) or dest.startswith('#'):continue
            target=(p.parent/dest.split('#',1)[0]).resolve()
            require(target.is_file() or target.is_dir(),'Broken local link: '+str(p.relative_to(ROOT))+' -> '+dest)
            links+=1
    bundle=load('examples/nonnegative/bundle.json')
    amap={a['id']:a for a in bundle['artifacts']}
    require(len(amap)==len(bundle['artifacts']),'Duplicate artifact ID')
    for a in bundle['artifacts']:
        require(safe_path(a['path']),'Unsafe artifact path')
        require((ROOT/a['path']).is_file(),'Missing artifact')
        require(hashlib.sha256((ROOT/a['path']).read_bytes()).hexdigest()==a['sha256'],'Artifact bytes changed: '+a['id'])
    require(set(bundle['entrypoints'].values())<=set(amap),'Missing entrypoint')
    context={'bundle':bundle}
    for key in ['ledger','graph','result','profile','oracle','spec','candidate']:
        context[key]=load(amap[bundle['entrypoints'][key]]['path'])
    require(not policy_errors(context),'Valid illustrative manifest rejected: '+str(policy_errors(context)))
    source=(ROOT/amap[context['ledger']['source_artifact_id']]['path']).read_text().strip()
    req_ids={x['id'] for x in context['ledger']['requirements']}
    case_ids={x['id'] for x in context['oracle']['expected_cases']}
    for r in context['ledger']['requirements']:
        span=r['source_span']
        require(0<=span['start']<=span['end']<=len(source),'Invalid source span')
        require(source[span['start']:span['end']]==r['source_excerpt'],'Requirement source excerpt mismatch')
        require(set(r['oracle_case_ids'])<=case_ids,'Unknown oracle case')
    for o in [load(amap['artifact-'+oid]['path']) for oid in bundle['obligation_ids']]:
        require(o['semantic_profile_id']==context['profile']['id'],'Obligation profile mismatch')
        require(set(o['requirements'])<=req_ids,'Unknown obligation requirement')
        require(o['source_artifact_id'] in amap,'Missing obligation source')
        require(o['target_artifact_id'] is None or o['target_artifact_id'] in amap,'Missing obligation target')
    for n in context['graph']['nodes']:
        require(n['artifact_id'] is None or n['artifact_id'] in amap,'Missing graph artifact')
    bad=load('benchmarks/negative-manifests.json')['cases']
    require(len({x['id'] for x in bad})==len(bad),'Duplicate negative case')
    for case in bad:
        altered=copy.deepcopy(context);target=altered[case['target']]
        for k in case['path'][:-1]:target=target[k]
        target[case['path'][-1]]=case['value']
        errors=policy_errors(altered)
        require(case['expected_error'] in errors,'Negative manifest accepted/misclassified: '+case['id']+' '+str(errors))
    profiles=load('eval/profiles.json')['profiles'];pids={p['id'] for p in profiles}
    require(len(pids)==len(profiles),'Duplicate evaluation profile')
    require(context['result']['acceptance']=='NotAccepted','Illustrative result cannot be accepted')
    run=load('eval/run-plan.example.json')
    require(run['budget_profile_id'] in pids and run['result_status']=='NotRun','Invalid eval plan')
    for p in profiles:
        if not p['model_required']:
            require(p['max_model_tokens']==0 and p['max_usd_per_task']==0,'Non-model profile has model spending')
    for route in load('profiles/backend-capabilities.json')['routes']:
        check_backend_status(route)
    refs=load('research/references.json')['references']
    require(len({r['id'] for r in refs})==len(refs),'Duplicate reference ID')
    report={'status':'passed','scope':'specification_consistency_only','schemas':len(schemas),'validated_instances':instances,
      'requirements':len(reg),'work_packages':len(wps),'negative_manifests_rejected':len(bad),'local_links':links,
      'reference_entries':len(refs),'compiler_runs':0,'solver_runs':0,'model_runs':0,'runtime_benchmarks':0}
    print(json.dumps(report,indent=2))
    if args.report:
        args.report.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('Specification check failed: '+str(e),file=sys.stderr);sys.exit(1)
