import json
import re


class Grammer:
    _nonterms = None
    _terms = None
    _start_term = None
    _productions = None

    def by_json(self, file_path):
        file = open(file_path)
        doc = json.load(file)
        
        self._nonterms = set(doc['nonterms'])
        self._terms = set(doc['terms'])
        self._productions = doc['productions']
        self._start_nonterm = doc['start_nonterm']

        return self
    
    def remove_unreachables(self):
        vs = [set(self._start_nonterm)]

        while True:
            v = set()
            
            for symbol in self._nonterms | self._terms:
                for key in self._productions:
                    if key not in vs[-1]:
                        continue
                    
                    for rhs in self._productions[key]:
                        if re.search(f'.*{re.escape(symbol)}.*', rhs):
                            v.add(symbol)

            vs.append(vs[-1] | v)

            if vs[-1] == vs[-2]:
                break
        
        self._nonterms = self._nonterms & vs[-1]
        self._terms = self._terms & vs[-1]
        
        productions = {}
        for key in self._productions:
            if key in self._nonterms:
                productions[key] = self._productions[key]
        self._productions = productions

        return self

    def __str__(self):
        return f'nonterms: {self._nonterms}, terms: {self._terms}, productions: {self._productions}, start_nonterm: {self._start_nonterm}'

def main():
    file_path = 'grammer.json'
    # file_path = input()

    grammer = Grammer().by_json(file_path).remove_unreachables()
    print(grammer)

if __name__ == '__main__':
    main()