"""Focused full-run planning, safety, and saved-data checks with synthetic rows."""
import csv
import hashlib
import json
from pathlib import Path

import pytest

import benchmark_memory_full as full
from analyze_memory_full import summarize, csv_rows


def fixture_rows():
    rows=[]
    for index,(family,size,repetition,mode) in enumerate(full.schedule(),1):
        rows.append(dict(observation=index,family=family,size=size,repetition=repetition,
                         evaluator=mode,pid=1000+index,status='ok',gc_enabled=True,
                         recursion_limit=1000,python='fixture',executable='fixture',platform='fixture',gc_thresholds=[2000,10,10],
                         correct=None if mode=='control' else True,evaluated=mode!='control',
                         control_input_preserved=mode=='control',result='7',expected='7',
                         baseline_bytes=100,peak_bytes=100+repetition,ending_bytes=100,
                         peak_growth_bytes=repetition,end_growth_bytes=0))
    return rows


def save_fixture(root, monkeypatch):
    rows=fixture_rows()
    (root/'observations').mkdir()
    for row in rows:
        (root/'observations'/f"{row['observation']:03}.json").write_text(json.dumps(row))
    (root/'raw_samples.json').write_text(json.dumps(rows))
    (root/'metadata.json').write_text(json.dumps(dict(expected_observations=180,recursion_limit=1000,
                                                   source_sha256={},earlier_evidence_sha256={})))
    (root/'errors.json').write_text('[]')
    with (root/'raw_samples.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=full.CSV_FIELDS,lineterminator='\n')
        writer.writeheader();writer.writerows(full.csv_projection(rows))
    return rows


def test_schedule_and_statistics():
    rows=fixture_rows()
    assert len(rows)==180
    assert sum(r['evaluator']=='control' for r in rows)==60
    assert [r['evaluator'] for r in rows[:6]]==['current','cek','control','cek','current','control']
    summary=summarize(rows)
    assert len(summary)==18
    for row in summary:
        assert row['successful']==10 and row['errors']==0
        assert row['peak_growth_median_bytes']==5.5
        assert row['peak_growth_q1_bytes']==3.25
        assert row['peak_growth_q3_bytes']==7.75
        assert row['peak_growth_iqr_bytes']==4.5
        assert row['peak_growth_min_bytes']==1 and row['peak_growth_max_bytes']==10


def test_saved_raw_verifier_and_tamper(tmp_path,monkeypatch):
    rows=save_fixture(tmp_path,monkeypatch)
    result=full.verify(tmp_path)
    assert result['status']=='passed' and result['correct_evaluations']==120
    rows[0]['peak_growth_bytes']=999
    (tmp_path/'raw_samples.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError):full.verify(tmp_path)


def test_missing_sample_rejected(tmp_path,monkeypatch):
    rows=save_fixture(tmp_path,monkeypatch)
    (tmp_path/'raw_samples.json').write_text(json.dumps(rows[:-1]))
    with pytest.raises(ValueError,match='Missing'):full.verify(tmp_path)


def test_source_and_evidence_hashes_checked(tmp_path,monkeypatch):
    save_fixture(tmp_path,monkeypatch)
    source=tmp_path/'source.py';source.write_text('original')
    meta=json.loads((tmp_path/'metadata.json').read_text())
    meta.update(source_commit='fixture',source_sha256={'source.py':hashlib.sha256(b'original').hexdigest()},
                earlier_evidence_sha256={'source.py':hashlib.sha256(b'original').hexdigest()})
    (tmp_path/'metadata.json').write_text(json.dumps(meta))
    monkeypatch.setattr(full,'ROOT',tmp_path)
    monkeypatch.setattr(full.subprocess,'check_output',lambda *args,**kwargs:b'original')
    assert full.verify(tmp_path)['status']=='passed'
    source.write_text('changed')
    with pytest.raises(ValueError,match='Working source'):full.verify(tmp_path)


def test_no_overwrite_or_dirty_run(tmp_path,monkeypatch):
    monkeypatch.setattr(full,'MEMORY_ROOT',tmp_path)
    monkeypatch.setattr(full,'git',lambda *args:'dirty' if args[0]=='status' else '')
    with pytest.raises(RuntimeError,match='clean'):full.collect(tmp_path/'run')
    assert not (tmp_path/'run').exists()
    monkeypatch.setattr(full,'git',lambda *args:'')
    (tmp_path/'existing').mkdir()
    sentinel=tmp_path/'existing'/'evidence';sentinel.write_text('preserved')
    with pytest.raises(FileExistsError):full.collect(tmp_path/'existing')
    assert sentinel.read_text()=='preserved'


def test_failed_sample_preserved_in_statistics():
    rows=fixture_rows();rows[0]['status']='worker_error'
    summary=summarize(rows)
    assert summary[0]['observations']==10 and summary[0]['successful']==9 and summary[0]['errors']==1
