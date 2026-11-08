"""Read only non-secret Git/deployment metadata from the authorized Vercel CLI."""
import json
import os
import subprocess
import argparse
from vercel_environment import base, config, root


def request(endpoint):
    result=subprocess.run(base+['api',endpoint,'--scope','resume-project3','--global-config',config],cwd=root,input=None,text=True,capture_output=True,env={**os.environ,'VERCEL_TELEMETRY_DISABLED':'1'})
    if result.returncode:
        raise RuntimeError('Could not read Vercel project metadata')
    return json.loads(result.stdout)


parser=argparse.ArgumentParser()
parser.add_argument('--commit')
args=parser.parse_args()
for name in ['regulatrust-api','regulatrust-ai']:
    project=request('/v9/projects/'+name)
    link=project.get('link') or {}
    print(json.dumps({'project':project['name'],'id':project['id'],'root_directory':project.get('rootDirectory'),'framework':project.get('framework'),'git':{key:link.get(key) for key in ['type','org','repo','repoId','productionBranch']}}))
    if args.commit:
        deployments=request('/v6/deployments?projectId='+project['id']+'&limit=10&target=production')
        matches=[]
        for deployment in deployments.get('deployments',[]):
            metadata=deployment.get('meta') or {}
            if metadata.get('githubCommitSha')==args.commit or (deployment.get('gitSource') or {}).get('sha')==args.commit:
                matches.append({'id':deployment.get('uid'),'url':deployment.get('url'),'state':deployment.get('readyState') or deployment.get('state'),'source':deployment.get('source'),'commit':metadata.get('githubCommitSha'),'branch':metadata.get('githubCommitRef')})
        print(json.dumps({'project':name,'matching_deployments':matches}))
