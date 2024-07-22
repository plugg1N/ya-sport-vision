from Utils.audio_dp import AudioDispatcher

AudioDispatcher().split_into_batches(file_name='10m_example.mp3',
                                     overlap_s=1,
                                     chunk_length=210)
