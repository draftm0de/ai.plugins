from tests.support.plugin_fixture import materialize
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'Makefile').is_file())
HELPER = ROOT/'skills/_shared/scripts/publish_plan.py'
SPEC=importlib.util.spec_from_file_location('publish_plan',HELPER)
plan=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(plan)

class PublishPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name).resolve();self.root=self.work/'source';self.root.mkdir();self.state=self.work/'private-journal'
        self.repo='https://github.com/example/fixture'
        (self.root/'plugin.json').write_text(json.dumps({'name':'fixture','repository':self.repo}))
        (self.root/'CHANGELOG.md').write_text('# Changelog\n\n## [0.1.0]\n\nFictional initial version.\n')
        (self.root/'.gitignore').write_text('.tmp/\ndist/\n')
        self.git('init','-q','--initial-branch=main');self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
        self.git('add','.');self.git('commit','-qm','fixture');self.git('remote','add','origin',self.repo)
        self.proposal={'files':['plugin.json','CHANGELOG.md'],
          'commit_message':'feat: fictional manager','pr_title':'Fictional manager','pr_body':'Fictional tested change',
          'branch':'improve-plugin-publication','base_branch':'main','default_branch':'main','repository':self.repo,'merge_method':'squash',
          'provider':'github-connector','capabilities':self.capabilities(),
          'base_commit':self.git('rev-parse','HEAD').decode().strip(),'base_evidence':'Fictional observed remote main branch',
          'checks':[{'name':'fixture','result':'passed','evidence':'fictional test log'}]}
    def capabilities(self):
        return {name:{'available':True,'evidence':'Fictional verified capability and permission: '+name} for name in plan.CAPABILITIES}
    def commit_approved(self):
        (self.root/'CHANGELOG.md').write_text('Fictional approved update')
        self.approve();plan.start_branch(self.state)
        plan.check_before_commit(plan.read(self.state))
        self.git('add','--','CHANGELOG.md');self.git('commit','-qm',self.proposal['commit_message'])
        return self.git('rev-parse','HEAD').decode().strip()
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.STDOUT)
    def prepare(self):return plan.prepare(self.root,self.proposal,self.state)
    def approve(self):
        result=self.prepare();return plan.approve(self.state,result['digest'],'Yes: approve message and all listed publication steps.', confirmed=True)
    def test_preparation_has_no_git_mutations_and_retry_is_identical(self):
        head=self.git('rev-parse','HEAD');status=self.git('status','--porcelain')
        first=self.prepare();self.assertEqual(first,self.prepare());self.assertEqual('prepared',first['stage'])
        self.assertEqual(head,self.git('rev-parse','HEAD'));self.assertEqual(status,self.git('status','--porcelain'))
    def test_denied_or_absent_approval_does_not_advance(self):
        data=self.prepare()
        with self.assertRaises(ValueError):plan.approve(self.state,data['digest'],'', confirmed=True)
        with self.assertRaises(ValueError):plan.checkpoint(self.state,'committed',{'commit':'b'*40})
        with self.assertRaises(ValueError):plan.approve(self.state,data['digest'],'No, do not publish', confirmed=False)
        self.assertEqual('prepared',plan.read(self.state)['stage'])
    def test_digest_mismatch_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):plan.approve(self.state,'wrong','yes', confirmed=True)
    def test_selected_file_drift_invalidates_approval(self):
        data=self.prepare();(self.root/'CHANGELOG.md').write_text('changed after review')
        with self.assertRaisesRegex(ValueError,'Source changed'):plan.approve(self.state,data['digest'],'yes', confirmed=True)
    def test_postapproval_drift_is_detected_before_commit(self):
        self.approve();(self.root/'plugin.json').write_text('{}')
        with self.assertRaises(ValueError):plan.ensure_current(plan.read(self.state))
    def test_unrelated_work_not_included_or_modified(self):
        (self.root/'unrelated.txt').write_text('keep private draft out')
        data=self.prepare();self.assertNotIn('unrelated.txt',data['plan']['snapshot']['files'])
        self.assertEqual('keep private draft out',(self.root/'unrelated.txt').read_text())
    def test_preexisting_index_preserved(self):
        (self.root/'staged.txt').write_text('preserve');self.git('add','staged.txt');before=self.git('diff','--cached','--binary')
        with self.assertRaisesRegex(ValueError,'staged'):self.prepare()
        self.assertEqual(before,self.git('diff','--cached','--binary'))
    def test_manifest_repository_conflict(self):
        (self.root/'plugin.json').write_text(json.dumps({'name':'fixture','repository':'https://github.com/example/other'}))
        with self.assertRaisesRegex(ValueError,'repository'):self.prepare()
    def test_version_and_legacy_journal_are_rejected(self):
        (self.root/'plugin.json').write_text(json.dumps({'name':'fixture','version':'1.0.0','repository':self.repo}))
        with self.assertRaisesRegex(ValueError,'omit'):self.prepare()
    def test_failed_check_blocks_plan(self):
        self.proposal['checks'][0]['result']='failed'
        with self.assertRaises(ValueError):self.prepare()
    def test_documentation_only_publish_needs_no_manifest_or_changelog_edit(self):
        (self.root/'README.md').write_text('Fictional documentation change')
        self.proposal['files']=['README.md']
        (self.root/'CHANGELOG.md').unlink()
        self.assertEqual(['README.md'],self.prepare()['plan']['proposal']['files'])
    def test_unselected_manifest_drift_invalidates_documentation_approval(self):
        (self.root/'README.md').write_text('Fictional docs')
        self.proposal['files']=['README.md']
        data=self.prepare()
        (self.root/'plugin.json').write_text(json.dumps({'name':'changed','repository':self.repo}))
        with self.assertRaisesRegex(ValueError,'Source changed'):plan.approve(self.state,data['digest'],'yes',confirmed=True)
    def test_legacy_journal_cannot_resume_under_new_workflow(self):
        data=self.prepare();data['plan']['schema_version']=1;data['digest']=plan.sha(plan.encoded(data['plan']))
        (self.state/'publication.json').write_bytes(plan.encoded(data))
        with self.assertRaisesRegex(ValueError,'Legacy publication journal'):plan.read(self.state)
    def test_unsafe_selected_files(self):
        for name in ('../outside','.env','.tmp/output','private.key'):
            self.proposal['files']=['plugin.json','CHANGELOG.md',name]
            with self.assertRaises(ValueError):self.prepare()
    def test_state_cannot_be_in_source_or_plugin(self):
        for state in (self.root/'private-state',HELPER.parent/'state'):
            with self.assertRaises(ValueError):plan.prepare(self.root,self.proposal,state)
    def test_tampered_plan_rejected(self):
        self.prepare();p=self.state/'publication.json';data=json.loads(p.read_text());data['plan']['proposal']['commit_message']='tampered';p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'integrity'):plan.read(self.state)
    def test_lock_conflict_preserves_existing_journal(self):
        self.prepare();before=(self.state/'publication.json').read_bytes();(self.state/'.lock').touch()
        with self.assertRaises(FileExistsError):self.prepare()
        self.assertEqual(before,(self.state/'publication.json').read_bytes())
    def test_changed_message_requires_new_plan(self):
        self.prepare();self.proposal['commit_message']='different proposal'
        with self.assertRaisesRegex(ValueError,'new approval'):self.prepare()
    def test_complete_journal_and_identical_retry(self):
        commit=self.commit_approved();merged='c'*40
        steps=[('committed',{'commit':commit}),('pushed',{'commit':commit,'branch':self.proposal['branch']}),
         ('pr_open',{'url':self.repo+'/pull/1','head':commit}),
         ('checks_passed',{'head':commit,'checks':[{'name':'test','result':'passed'}]}),
         ('merged',{'commit':merged,'url':self.repo+'/pull/1'})]
        for stage,evidence in steps:
            current=plan.checkpoint(self.state,stage,evidence);self.assertEqual(current,plan.checkpoint(self.state,stage,evidence))
        self.assertEqual('merged',plan.read(self.state)['stage'])
        self.assertEqual('merged',plan.start_branch(self.state)['stage'])
        with self.assertRaises(ValueError):plan.checkpoint(self.state,'released',{'commit':merged})
    def test_changed_remote_head_and_failed_checks_stop(self):
        commit=self.commit_approved();plan.checkpoint(self.state,'committed',{'commit':commit})
        with self.assertRaises(ValueError):plan.checkpoint(self.state,'pushed',{'commit':'c'*40,'branch':self.proposal['branch']})
        plan.checkpoint(self.state,'pushed',{'commit':commit,'branch':self.proposal['branch']})
        plan.checkpoint(self.state,'pr_open',{'head':commit,'url':self.repo+'/pull/1'})
        with self.assertRaises(ValueError):plan.checkpoint(self.state,'checks_passed',{'head':commit,'checks':[{'result':'pending'}]})
    def test_extracted_runtime_prepares_without_manager_checkout(self):
        installed=materialize(self.work/'installed')
        proposal=self.work/'proposal.json';proposal.write_text(json.dumps(self.proposal))
        helper=installed/'skills/_shared/scripts/publish_plan.py'
        result=subprocess.run([sys.executable,'-B',str(helper),'prepare','--source',str(self.root),'--proposal',str(proposal),'--state-dir',str(self.state)],cwd=self.work,capture_output=True,text=True,check=True)
        self.assertEqual('prepared',json.loads(result.stdout)['stage'])

    def test_marketplace_plan_needs_observed_new_plugin_publication(self):
        (self.root/'plugin.json').unlink()
        catalog={'name':'fixture-market','plugins':[{'name':'new-plugin','repository':'https://github.com/example/new-plugin.git'}]}
        (self.root/'marketplace.json').write_text(json.dumps(catalog))
        self.proposal['files']=['marketplace.json']
        with self.assertRaisesRegex(ValueError,'Publish and verify'):
            self.prepare()
        self.proposal['dependencies']=[{'repository':'https://github.com/example/new-plugin','commit':'a'*40,'evidence':'Fictional observed merge and remote structure for this test'}]
        data=self.prepare()
        self.assertIn('marketplace.json',data['plan']['snapshot']['metadata'])
        catalog['name']='changed-after-review'
        (self.root/'marketplace.json').write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError,'Source changed'):
            plan.approve(self.state,data['digest'],'Fictional test approval',confirmed=True)

    def test_local_mapping_cannot_be_published_even_without_gitignore(self):
        (self.root/'.local').mkdir()
        (self.root/'.local/marketplace.json').write_text('{}')
        self.proposal['files']=['.local/marketplace.json']
        with self.assertRaisesRegex(ValueError,'Private/generated'):
            self.prepare()

    def test_codex_manifest_add_change_remove_invalidates_approval(self):
        path=self.root/'.codex-plugin/plugin.json';path.parent.mkdir()
        for mutation in ('add','change','remove'):
            with self.subTest(mutation=mutation):
                self.state=self.work/('journal-'+mutation)
                path.unlink(missing_ok=True)
                if mutation != 'add': path.write_text('{"name":"fixture"}')
                data=self.approve()
                self.assertIn('.codex-plugin/plugin.json',data['plan']['snapshot']['metadata'])
                self.assertNotIn('.codex-plugin/plugin.json',self.proposal['files'])
                if mutation=='remove': path.unlink()
                else: path.write_text('{"name":"changed"}')
                with self.assertRaisesRegex(ValueError,'Source changed'):
                    plan.ensure_current(plan.read(self.state))

    def test_pr_requires_available_observed_base(self):
        for field,value in (('base_commit','a'*40),('base_evidence','')):
            original=self.proposal[field];self.proposal[field]=value
            with self.assertRaises(ValueError):self.prepare()
            self.proposal[field]=original
        self.proposal.pop('base_commit')
        with self.assertRaisesRegex(ValueError,'base_commit'):self.prepare()

    def test_unborn_initial_publication_for_both_repository_types(self):
        for kind in ('plugin','marketplace'):
            with self.subTest(kind=kind):
                self.root=self.work/kind;self.root.mkdir()
                self.state=self.work/(kind+'-journal')
                self.git('init','-q','--initial-branch=main')
                self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
                self.git('remote','add','origin',self.repo)
                manifest={'name':'fixture','repository':self.repo}
                if kind=='marketplace':manifest['plugins']=[]
                filename=kind+'.json';(self.root/filename).write_text(json.dumps(manifest))
                before=self.git('status','--porcelain')
                old=self.proposal
                with self.assertRaisesRegex(ValueError,'No HEAD'):self.prepare()
                self.proposal={'publication_mode':'initial','files':[filename],
                    'commit_message':'Initial fictional '+kind,'branch':'main','repository':self.repo,
                    'remote_empty_evidence':'Fictional empty local bare remote inspected; no existing heads',
                    'provider':'github-connector','capabilities':self.capabilities(),
                    'checks':[{'name':'fixture','result':'passed','evidence':'Fictional pre-publication check'}]}
                data=self.prepare()
                self.assertIsNone(data['plan']['snapshot']['head'])
                self.assertEqual(before,self.git('status','--porcelain'))
                self.assertIsNone(plan.head(self.root))
                with self.assertRaisesRegex(ValueError,'initial publication approval'):
                    plan.approve(self.state,data['digest'],'Fictional test consent',confirmed=True)
                approved=plan.approve(self.state,data['digest'],'Fictional explicit initial commit and direct push consent',confirmed=True,confirm_initial=True)
                plan.ensure_current(approved)
                with self.assertRaises(ValueError):plan.checkpoint(self.state,'pushed',{'commit':'a'*40,'branch':'main'})
                # Actual commit/push only in fictional temporary test repositories.
                remote=self.work/(kind+'-remote.git')
                subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
                self.git('add','--',filename);self.git('commit','-qm',self.proposal['commit_message'])
                commit=self.git('rev-parse','HEAD').decode().strip()
                self.assertEqual(commit,self.git('rev-list','--max-parents=0','HEAD').decode().strip())
                plan.checkpoint(self.state,'committed',{'commit':commit})
                self.git('push',str(remote),'HEAD:refs/heads/main')
                observed=subprocess.check_output(['git','--git-dir',str(remote),'rev-parse','refs/heads/main'],text=True).strip()
                plan.checkpoint(self.state,'pushed',{'commit':observed,'branch':'main'})
                with self.assertRaises(ValueError):plan.checkpoint(self.state,'pr_open',{'head':commit,'url':self.repo+'/pull/1'})
                receipt={'commit':observed,'branch':'main','checks':[{'name':'fixture','result':'passed'}],
                         'remote_evidence':'Observed fictional local bare main ref and compared committed tree'}
                result=plan.checkpoint(self.state,'published',receipt)
                self.assertEqual('published',result['stage'])
                self.assertEqual(result,plan.checkpoint(self.state,'published',receipt))
                self.proposal=old

    def test_initial_mode_never_applies_to_existing_history(self):
        self.proposal={'publication_mode':'initial','files':['plugin.json'],'commit_message':'Fixture',
                       'branch':'main','repository':self.repo,'remote_empty_evidence':'Fixture',
                       'provider':'github-connector','capabilities':self.capabilities(),
                       'checks':[{'name':'test','result':'passed','evidence':'Fixture'}]}
        with self.assertRaisesRegex(ValueError,'unborn'):self.prepare()

    def test_regular_branch_is_explicit_separate_and_not_host_prefixed(self):
        for branch in ('main','codex/change','claude/change'):
            with self.subTest(branch=branch):
                self.proposal['branch']=branch
                with self.assertRaisesRegex(ValueError,'separate feature branch'):self.prepare()
        self.proposal['base_branch']='release'
        self.proposal['branch']='main'
        with self.assertRaisesRegex(ValueError,'separate feature branch'):self.prepare()

    def test_feature_branch_created_only_after_approval_and_reused(self):
        before=self.git('show-ref')
        self.prepare()
        with self.assertRaisesRegex(ValueError,'approval'):plan.start_branch(self.state)
        self.assertEqual(before,self.git('show-ref'))
        self.approve()
        with self.assertRaises(ValueError):plan.check_before_commit(plan.read(self.state))
        first=plan.start_branch(self.state)
        self.assertEqual('branched',first['stage'])
        self.assertEqual(self.proposal['branch'],plan.active_branch(self.root))
        self.assertEqual(first,plan.start_branch(self.state))
        plan.check_before_commit(first)
        self.git('switch','main')
        with self.assertRaisesRegex(ValueError,'approved branch'):plan.check_before_commit(first)
        self.assertEqual(first,plan.start_branch(self.state))
        self.assertEqual(self.proposal['branch'],plan.active_branch(self.root))

    def test_existing_unowned_branch_and_changed_resumed_branch_are_rejected(self):
        self.approve();self.git('branch',self.proposal['branch'])
        with self.assertRaisesRegex(ValueError,'outside this publication'):plan.start_branch(self.state)
        self.git('branch','-D',self.proposal['branch'])
        plan.start_branch(self.state)
        self.git('commit','--allow-empty','-qm','Unapproved fictional change')
        with self.assertRaisesRegex(ValueError,'Source changed'):plan.start_branch(self.state)

    def test_branch_intent_recovers_interruption_without_creating_another_branch(self):
        self.approve();real_write=plan.write
        def interrupted(path,data):
            if data['stage']=='branched':raise OSError('Fictional interruption after git switch')
            return real_write(path,data)
        with patch.object(plan,'write',side_effect=interrupted):
            with self.assertRaises(OSError):plan.start_branch(self.state)
        self.assertEqual('approved',plan.read(self.state)['stage'])
        self.assertEqual(self.proposal['branch'],plan.active_branch(self.root))
        self.assertEqual('branched',plan.start_branch(self.state)['stage'])

    def test_changed_branch_name_requires_new_plan_and_approval(self):
        self.approve();self.proposal['branch']='another-reviewed-change'
        with self.assertRaisesRegex(ValueError,'new approval'):self.prepare()
        self.assertEqual('main',plan.active_branch(self.root))

    def test_commit_on_default_branch_cannot_be_recorded(self):
        self.approve();plan.start_branch(self.state);self.git('switch','main')
        self.git('commit','--allow-empty','-qm','Wrong branch fictional fixture')
        with self.assertRaisesRegex(ValueError,'approved active branch'):
            plan.checkpoint(self.state,'committed',{'commit':plan.head(self.root)})
        self.assertEqual('branched',plan.read(self.state)['stage'])

    def test_missing_provider_capability_is_reported_without_mutations(self):
        before=self.git('show-ref')
        for name in plan.CAPABILITIES:
            self.proposal['capabilities']=self.capabilities()
            self.proposal['capabilities'][name]['available']=False
            with self.assertRaisesRegex(ValueError,name):self.prepare()
        self.assertEqual(before,self.git('show-ref'))
        self.assertFalse(self.state.exists())
        self.proposal['capabilities']=self.capabilities();self.proposal['provider']='gh'
        self.assertEqual('prepared',self.prepare()['stage'])

    def test_deleted_resumed_branch_is_not_recreated(self):
        self.approve();plan.start_branch(self.state)
        self.git('switch','main');self.git('branch','-D',self.proposal['branch'])
        with self.assertRaisesRegex(ValueError,'missing'):plan.start_branch(self.state)
        self.assertFalse(plan.ref_exists(self.root,'refs/heads/'+self.proposal['branch']))

if __name__=='__main__':unittest.main()
