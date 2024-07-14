extern "C" {
#include <libavformat/avformat.h>
}

#include <iostream>
#include <thread>
#include <vector>
#include <string>
#include <sstream>

void run_ffmpeg(int i, double start_time, double chunk_length, double overlap_s, std::string file_name) {
    std::ostringstream command;
    command << "ffmpeg -hide_banner -loglevel error -ss " << start_time
            << " -i " << file_name << " -ac 1 -ar 16000 -t " << chunk_length
            << " segments/chunk_" << i << ".wav -y";
    std::system(command.str().c_str());
}



int get_audio_duration(const std::string& filename) {
    AVFormatContext* formatContext = avformat_alloc_context();
    if (!formatContext) {
        throw std::runtime_error("Could not allocate memory for Format Context");
    }

    if (avformat_open_input(&formatContext, filename.c_str(), nullptr, nullptr) != 0) {
        avformat_free_context(formatContext);
        throw std::runtime_error("Could not open the file");
    }

    if (avformat_find_stream_info(formatContext, nullptr) < 0) {
        avformat_close_input(&formatContext);
        throw std::runtime_error("Could not get the stream info");
    }

    double duration = formatContext->duration / (double)AV_TIME_BASE;

    avformat_close_input(&formatContext);

    return static_cast<int>(duration);
}





int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Not enough args provided" << std::endl;
    }

    const std::string file_name = argv[1];
    const int overlap_s = std::stoi(argv[2]);
    const int chunk_length = std::stoi(argv[3]);
    int video_duration = get_audio_duration(file_name);

    int iterable_cs = 0;
    int i = 1;

    std::vector<std::thread> threads;


    while (iterable_cs < video_duration) {
        threads.emplace_back(run_ffmpeg, i, iterable_cs, chunk_length, overlap_s, file_name);

        iterable_cs += chunk_length;
        i++;
    }


    for (auto& th : threads) {
        if (th.joinable()) {
            th.join();
        }
    }


    std::cout << "Finished chunking." << std::endl;
    return 0;
}

