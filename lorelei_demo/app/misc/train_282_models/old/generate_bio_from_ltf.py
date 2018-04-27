import io
import os
import subprocess

languages = ['ben', 'tam', 'tgl', 'tha', 'yor']

for lan in languages:
	dp = lan
	test_filelist_fp = os.path.join(dp, 'test_filelist')
	test_filelist = open(test_filelist_fp).read().strip().splitlines()
	ltf_filelist = [item for item in os.listdir(os.path.join(dp, 'ltf')) if 'ltf' in item]

	train_filelist = [item for item in ltf_filelist if item not in test_filelist]

	train_filelist_fp = os.path.join(dp, 'train_filelist')
	f = open(train_filelist_fp, 'w')
	f.write('\n'.join(train_filelist))
	f.close()

	ltflaf2bio_script_fp = '/Users/boliangzhang/Documents/Phd/Wheels/ietk/fmtconvtr/ltflaf2bio.py'

	ltf_dp = os.path.join(dp, 'ltf')
	laf_dp = os.path.join(dp, 'laf')

	bio_dir = os.path.join(dp, 'bio')
	if not os.path.exists(bio_dir):
		os.mkdir(bio_dir)

	# generate train.bio
	output_fp = os.path.join(bio_dir, 'train.bio')
	cmd = ['python', ltflaf2bio_script_fp, '--ltf_filelist_fp', train_filelist_fp, ltf_dp, laf_dp, output_fp]
	print ' '.join(cmd)
	subprocess.call(cmd)

	# generate test.bio
	output_fp = os.path.join(bio_dir, 'test.bio')
	cmd = ['python', ltflaf2bio_script_fp, '--ltf_filelist_fp', test_filelist_fp, ltf_dp, laf_dp, output_fp]
	print ' '.join(cmd)
	subprocess.call(cmd)


