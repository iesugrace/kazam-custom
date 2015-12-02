"""
Author: Joshua Chen
Date: 2015-10-10
Location: Shenzhen
Description: remove the noise of an video file, specialize for
the Kazam screen recorder. Audio codec is supposed to be mp3,
the first 1 second audio is used as noise for cleaning the audio.

Procedure:

1. 取出視頻
ffmpeg -i source.mp4 -vcodec copy -an video.mp4

2. 取出音頻
ffmpeg -i source.mp4 -vn -acodec copy audio.mp3

3. 截取一段空白的音頻
ffmpeg -i audio.mp3 -acodec copy -ss 00:27:31 -t 00:00:03 noise.mp3

4. 生成噪音描述信息
sox noise.mp3 -n noiseprof noise.prof

5. 去除噪音
sox audio.mp3 audio-clean.mp3 noisered noise.prof 0.21

6. 合並視頻和音頻
ffmpeg -i video.mp4 -i audio-clean.mp3 -vcodec copy -acodec copy merged.mp4

"""

import os
import tempfile

class Sox:
    avprog       = 'ffmpeg'
    soxprog      = 'sox'
    audio_suffix = 'mp3'
    video_suffix = 'mp4'
    noise_len    = '00:00:01'
    noise_sens   = 0.21

    def __init__(self, infile, outfile=None, overwrite=False):
        self.infile  = infile
        self.outfile = infile if overwrite else outfile

    def clean(self):
        video_only_file = self.extract_video()
        audio_only_file = self.extract_audio()
        noise_sample    = self.get_noise_sample(audio_only_file)
        noise_profile   = self.gen_noise_profile(noise_sample)
        clean_audio     = self.remove_noise(audio_only_file, noise_profile, self.noise_sens)
        self.merge(video_only_file, clean_audio)
        for f in (video_only_file, audio_only_file, noise_sample, noise_profile, clean_audio):
            os.unlink(f)

    def incrvol(self, factor=1.5):
        video_only_file = self.extract_video()
        audio_only_file = self.extract_audio()
        louder_audio    = self.increase_volume(audio_only_file, factor)
        self.merge(video_only_file, louder_audio)
        for f in (video_only_file, audio_only_file, louder_audio):
            os.unlink(f)

    def extract_video(self):
        return self.__extract(None, 'copy', self.video_suffix)

    def extract_audio(self):
        return self.__extract('copy', None, self.audio_suffix)

    def __extract(self, acodec, vcodec, suffix):
        outfile = tempfile.NamedTemporaryFile(delete=False).name + '.' + suffix
        if acodec:
            acodec_str = '-acodec %s' % acodec
        else:
            acodec_str = '-an'
        if vcodec:
            vcodec_str = '-vcodec %s' % vcodec
        else:
            vcodec_str = '-vn'

        cmd = '%s -y -i %s %s %s %s' % (self.avprog, self.infile, acodec_str, vcodec_str, outfile)
        return self.exec_shell_cmd_for_file(cmd, outfile)

    def exec_shell_cmd_for_file(self, cmd, outfile):
        if os.system(cmd) == 0:
            return outfile
        else:
            os.unlink(outfile)
            raise Exception

    def get_noise_sample(self, audio):
        outfile = tempfile.NamedTemporaryFile(delete=False).name + '.' + self.audio_suffix
        cmd = '%s -y -i %s -acodec copy -ss 00:00:00 -t %s %s' % (self.avprog, audio, self.noise_len, outfile)
        return self.exec_shell_cmd_for_file(cmd, outfile)

    def gen_noise_profile(self, sample):
        outfile = tempfile.NamedTemporaryFile(delete=False).name + '.prof'
        cmd = '%s %s -n noiseprof %s' % (self.soxprog, sample, outfile)
        return self.exec_shell_cmd_for_file(cmd, outfile)

    def remove_noise(self, audio, profile, sensitivity):
        outfile = tempfile.NamedTemporaryFile(delete=False).name + '.' + self.audio_suffix
        cmd = '%s %s %s noisered %s %s' % (self.soxprog, audio, outfile, profile, sensitivity)
        return self.exec_shell_cmd_for_file(cmd, outfile)

    def merge(self, video, audio):
        cmd = '%s -y -i %s -i %s -vcodec copy -acodec copy %s' % (self.avprog, video, audio, self.outfile)
        return self.exec_shell_cmd_for_file(cmd, self.outfile)

    def increase_volume(self, audio, factor):
        outfile = tempfile.NamedTemporaryFile(delete=False).name + '.' + self.audio_suffix
        cmd = '%s -v %s %s %s' % (self.soxprog, factor, audio, outfile)
        return self.exec_shell_cmd_for_file(cmd, outfile)


if __name__ == '__main__':
    import sys

    do_clean = True

    if '-v' in sys.argv:
        idx = sys.argv.index('-v')
        sys.argv.pop(idx)                   # remove the '-v'
        factor = float(sys.argv.pop(idx))   # get the factor number
        do_clean = False
    elif '-c' in sys.argv:
        idx = sys.argv.index('-c')
        sys.argv.pop(idx)                   # remove the '-c'
    else:
        print('Clean the noise:')
        print('%s -c IN-FILE OUT-FILE' % os.path.basename(sys.argv[0]))
        print('\nIncrease the volume')
        print('%s -v FACTOR IN-FILE OUT-FILE' % os.path.basename(sys.argv[0]))
        exit(1)

    infile, outfile = sys.argv[1:]
    sox = Sox(infile, outfile)
    if do_clean:
        sox.clean()
    else:
        sox.incrvol(factor)

