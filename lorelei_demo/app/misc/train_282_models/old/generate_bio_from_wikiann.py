import io
import os
from random import shuffle

wikiann_dir = '/nas/data/m1/zhangb8/lorelei/data/reference/282_edl/bio'

# languages = ['ben', 'tam', 'tgl', 'tha', 'yor']
# languages = [item.replace('.bio', '') for item in os.listdir(wikiann_dir) if item != '.DS_Store']
languages = ['cr']

current_languages = set(os.listdir('.'))

for lan in languages[:]:
	if lan in current_languages:
		continue

	print('processing %s ...' % lan)

	# create directory for new language
	os.mkdir(lan)
	bio_dp = os.path.join(lan, 'bio')
	os.mkdir(bio_dp)

	wikiann_bio_fp = os.path.join(wikiann_dir, 'wikiann-%s.bio' % lan)

	wikiann_bio = io.open(wikiann_bio_fp, 'r', -1, 'utf-8').read()

	res = []
	sents = wikiann_bio.split('\n\n')
	shuffle(sents)

	sent_threshold = 20000

	for line in sents:
		words = line.split('\n')
		if len(words) > 0 and len(words) < 30:
			res.append('\n'.join(words))
		if len(res) > sent_threshold:
			break

	if sent_threshold > len(res):
		sent_threshold = len(res)

	train_bio_fp = os.path.join(bio_dp, 'train.bio')
	f_out = io.open(train_bio_fp, 'w', -1, 'utf-8')
	f_out.write('\n\n'.join(res[:int(0.7 * sent_threshold)]))
	f_out.close()

	dev_bio_fp = os.path.join(bio_dp, 'dev.bio')
	f_out = io.open(dev_bio_fp, 'w', -1, 'utf-8')
	f_out.write('\n\n'.join(res[int(0.7 * sent_threshold):]))
	f_out.close()

	test_bio_fp = os.path.join(bio_dp, 'test.bio')
	f_out = io.open(test_bio_fp, 'w', -1, 'utf-8')
	f_out.write('\n\n'.join(res[int(0.7 * sent_threshold):]))
	f_out.close()


