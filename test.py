from novel_scrapper import *

novel = Novel("Keyboard Immortal", toc_main_link="https://novelusb.com/novel-book/keyboard-immortal-novel-novel")
novel.update_toc()
print(novel.toc_link_list)