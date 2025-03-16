#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

using namespace std;

int main() {
  const char *data_dir_raw = getenv("DATA_DIR");

  if (data_dir_raw == NULL) {
    cout << "DATA_DIR not set." << '\n';
    return 1;
  }

  cout << "Your DATA_DIR is: " << data_dir_raw << '\n';

  string data_dir(data_dir_raw);
  string data_file("data.json");

  string file_path = data_dir + string("/") + data_file;

  ifstream f(file_path);
  if (!f.is_open()) {
    cerr << "Error opening the file!";
    return 1;
  }

  string file_data;

  while (getline(f, file_data))
    cout << file_data << endl;

  // Close the file
  f.close();

  while (true) {
    sleep(1);
    cout << "Waiting to shut down..." << endl;
  }

  return 0;
}
