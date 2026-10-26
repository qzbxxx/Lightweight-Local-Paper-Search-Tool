import tkinter as tk
from tkinter import messagebox, scrolledtext
import pdf_loader
import api_service

class LiteratureAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("本地文献检索 Agent")
        self.root.geometry("700x550")

        self.papers_data = {}
        self.setup_ui()
        self.refresh_papers()

    def setup_ui(self):
        # 1. 顶部操作栏
        top_frame = tk.Frame(self.root, padx=10, pady=5)
        top_frame.pack(fill="x")
        
        self.lbl_status = tk.Label(top_frame, text="正在初始化...", fg="#555")
        self.lbl_status.pack(side="left")
        
        tk.Button(top_frame, text="🔄 刷新文献库", command=self.refresh_papers).pack(side="right")

        # 2. 提问区
        q_frame = tk.LabelFrame(self.root, text="询问需求", padx=10, pady=8)
        q_frame.pack(fill="x", padx=10, pady=5)

        self.query_entry = tk.Entry(q_frame, font=("Arial", 11))
        self.query_entry.pack(fill="x", pady=5)
        self.query_entry.bind("<Return>", lambda e: self.do_search())

        self.btn_search = tk.Button(q_frame, text="🚀 开始匹配文献", bg="#007bff", fg="white", font=("bold", 10), command=self.do_search)
        self.btn_search.pack(pady=3)

        # 3. 结果显示区
        res_frame = tk.LabelFrame(self.root, text="检索结果", padx=10, pady=5)
        res_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.res_box = scrolledtext.ScrolledText(res_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.res_box.pack(fill="both", expand=True)

    def refresh_papers(self):
        """重新扫描'文献'文件夹"""
        self.papers_data = pdf_loader.scan_all_papers()
        count = len(self.papers_data)
        self.lbl_status.config(text=f"当前已载入文献: {count} 篇 (位于'文献'文件夹)")
        
        self.res_box.delete(1.0, tk.END)
        if count == 0:
            self.res_box.insert(tk.END, "⚠️ 提示：【文献】文件夹中目前没有任何 PDF 论文，请放入文献后再试。\n")
        else:
            self.res_box.insert(tk.END, f"✅ 文献库就绪，共计 {count} 篇。请在上方输入你的需求进行查找。\n" + "-"*50 + "\n")

    def do_search(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("提示", "请输入查询需求！")
            return
        if not self.papers_data:
            messagebox.showwarning("提示", "文献库中没有找到 PDF 文件！")
            return

        self.res_box.insert(tk.END, f"\n🔎 正在匹配「{query}」...\n")
        self.root.update()

        try:
            # 静默调用 api_service
            ans = api_service.ask_agent(query, self.papers_data)
            self.res_box.insert(tk.END, ans + "\n\n")
            self.res_box.see(tk.END)
        except Exception as e:
            messagebox.showerror("发生错误", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = LiteratureAgentApp(root)
    root.mainloop()